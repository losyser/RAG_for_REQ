from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from cooling_rag_mg.config import get_config
from cooling_rag_mg.llm_cache import cached_completion
from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import safe_text, truncate


# ─────────────────────────────────────────────
# 改进的 prompt：结构化上下文，减少幻觉
# ─────────────────────────────────────────────
JUDGE_PROMPT = """
你是船舶主机冷却水系统 RAG 证据审查专家。

## 任务
判断候选证据列表中，哪些能支撑给定的工程子需求，哪些不能。

## 输入说明
- sub_requirement：当前需要检索证据的工程子需求，包含类型、主题和文本。
- candidates：候选证据列表，每条包含：
  - id：证据编号
  - text：证据原文（已截断）
  - applicability_constraints：适用性过滤阶段给出的约束说明（重要！）
  - key_metadata：关键元数据摘要
- max_selected：最多保留的证据条数。

## 判断规则（必须严格遵守）

### 关于 support_type
- **direct**：证据原文明确给出当前需求所需的对象、参数限值、配置要求、程序步骤或船级社义务。必须能直接转化为 shall 语句。
- **indirect**：证据内容相关，但缺少具体数值、适用范围，或需要结合其他文件才能形成工程要求。
- **background**：背景信息，说明原理、问题成因、行业惯例，不能作为主证据。
- **not_applicable**：内容不相关，或被 applicability_constraints 明确排除。

### 硬规则（违反任何一条 → 不得判为 direct）
1. evidence_strength = background 的证据 → 最高只能判为 background。
2. is_generalizable = no 的证据 → 不得跨厂家、机型、系统使用。
3. 来源为 paper 或 patent → 不得单独作为工程强制要求。
4. applicability_constraints 中明确说明"禁止判为 direct"→ 严格遵守。
5. 证据只描述系统组成或原理，未给出参数限值、施工步骤、验收判据 → 最高判为 indirect。
6. 子需求要求施工、冲洗、试压、支架、焊接 → 证据必须在 can_support 中包含 installation、flushing、pressure_test 或 inspection，否则最高 indirect。
7. 子需求要求温度/压力/流量具体数值 → 证据必须明确给出对应参数，否则最高 indirect，并在 reason 中说明"具体数值需查厂家技术数据"。
8. evidence_strength = background 的证据 → 必须放入 rejected，不得出现在 selected，无论主题多相近。
9. selected 数量不需要接近 max_selected。0 条、1 条、2 条都是正常结果。
   没有能直接或明确间接支撑本子需求核心工程动作的证据时，selected 应为空列表。

### 选择策略
- 只保留能直接给出参数限值、规则义务、施工步骤、配置要求或验收判据的证据（direct）；
  或虽缺少具体数值、但内容明确相关且能间接支撑本子需求核心方面的证据（indirect）。
- 以下情况必须放入 rejected，不得进入 selected：
  · evidence_strength = background（绝对禁止）
  · 来源为 paper 或 patent，且内容没有明确的直接间接支撑关系
  · 证据只描述背景原理、系统组成、问题成因或行业通行做法，没有工程约束力
  · 证据主题与子需求的核心对象和核心动作仅有词汇重叠，缺乏实质支撑
- 优先选 evidence_strength=direct、source_type 为规则或厂家手册的证据。
- 同一个来源文档最多保留 2 条。
- 不相关或已被 applicability_constraints 排除的证据放入 rejected，并说明原因。

## 输出格式（合法 JSON，不包含 Markdown）
{
  "selected": [
    {
      "id": "E-PUMP-CAP-001",
      "support_type": "direct",
      "evidence_role": "primary",
      "relevance": "high",
      "reason": "证据原文明确给出了XXX要求，直接支撑本需求的YYY方面。"
    }
  ],
  "rejected": [
    {
      "id": "E-SYS-XXX-001",
      "support_type": "not_applicable",
      "reason": "证据来源为论文，不能作为工程强制要求；且 applicability_constraints 已标注不适用。"
    }
  ]
}
"""


def _build_compact_candidate(c: dict[str, Any]) -> dict[str, Any]:
    """
    构建送给 LLM 的紧凑候选证据结构。

    改进：
    - 把 applicability_constraints 放在显眼位置
    - key_metadata 提炼最关键字段，不截断关键约束字段
    - text 截断到 800 字
    """
    metadata = normalize_v2_metadata(c.get("metadata", {}) or {})
    judge_appl = c.get("applicability", {}) or {}
    constraints = judge_appl.get("constraints", []) or []
    reasons_appl = judge_appl.get("reasons", []) or []

    # 关键约束：不能支撑的需求完整保留（最多 300 字）
    unsupported = safe_text(metadata.get("unsupported_requirements"))
    if len(unsupported) > 300:
        unsupported = unsupported[:300] + "…"

    # 整理说明完整保留（最多 300 字）
    summary = safe_text(metadata.get("normalized_summary"))
    if len(summary) > 300:
        summary = summary[:300] + "…"

    return {
        "id": c.get("id"),
        "text": truncate(c.get("text", ""), 800),
        "applicability_constraints": constraints,          # 过滤层给出的约束（最重要）
        "applicability_reasons": reasons_appl,            # 过滤层给出的原因
        "key_metadata": {
            "topic": metadata.get("topic", ""),
            "source_document": metadata.get("source_document", ""),
            "source_type": metadata.get("source_type", ""),
            "location": metadata.get("location", ""),
            "evidence_strength": metadata.get("evidence_strength", ""),
            "is_generalizable": metadata.get("is_generalizable", ""),
            "applicability_level": metadata.get("applicability_level", ""),
            "manufacturer": metadata.get("manufacturer", ""),
            "engine_model": metadata.get("engine_model", ""),
            "system_type": metadata.get("system_type", []),
            "component_objects": metadata.get("component_objects", []),
            "requirement_intents": metadata.get("requirement_intents", []),
            "engineering_phase": metadata.get("engineering_phase", []),
            "applicable_condition": metadata.get("applicable_condition", []),
            "can_support": metadata.get("can_support", []),
            "limitation": metadata.get("limitation", ""),
            "normalized_summary": summary,
            "supportable_requirements": metadata.get("supportable_requirements", []),
            "unsupported_requirements": unsupported,       # 完整保留（最多 300 字）
        },
        "profile_match_summary": {
            "matched_components": c.get("profile_match", {}).get("matched_components", []),
            "matched_aspects": c.get("profile_match", {}).get("matched_aspects", []),
            "matched_can_support": c.get("profile_match", {}).get("matched_can_support", []),
        },
    }


def judge_evidence(
    sub_requirement: dict[str, Any],
    candidates: list[dict[str, Any]],
    max_selected: int = 5,
) -> dict[str, Any]:
    cfg = get_config()
    if not cfg.deepseek.enabled or not cfg.deepseek.use_evidence_judge:
        return fallback_judge(candidates, max_selected)

    try:
        compact_candidates = [_build_compact_candidate(c) for c in candidates[:25]]

        payload = {
            "sub_requirement": {
                "sub_requirement_id": sub_requirement.get("sub_requirement_id", ""),
                "requirement_type": sub_requirement.get("requirement_type", ""),
                "topic": sub_requirement.get("topic", ""),
                "text": sub_requirement.get("text", ""),
            },
            "max_selected": max_selected,
            "candidates": compact_candidates,
        }

        client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
        resp = cached_completion(
            client,
            model=cfg.deepseek.model,
            messages=[
                {"role": "system", "content": JUDGE_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=cfg.deepseek.temperature,
            max_tokens=cfg.deepseek.max_tokens_judge,
            response_format={"type": "json_object"},
        )
        obj = json.loads(resp.choices[0].message.content or "{}")
        selected = obj.get("selected", [])[:max_selected]
        return {
            "selected": selected,
            "rejected": obj.get("rejected", []),
            "judge_method": "deepseek",
        }
    except Exception as exc:
        result = fallback_judge(candidates, max_selected)
        result["judge_error"] = str(exc)
        return result


def fallback_judge(
    candidates: list[dict[str, Any]],
    max_selected: int,
) -> dict[str, Any]:
    """
    无 LLM 时的降级判断。

    改进：
    - 阈值 0.65（profile 分数叠加后的合理阈值；原始阈值 0.70 过高）
    - 优先选 direct strength 的证据
    - 最多 max_selected 条
    """
    selected = []
    rejected = []

    # 按分数排序，优先处理高分证据
    sorted_candidates = sorted(candidates, key=lambda x: float(x.get("final_score", 0.0) or 0.0), reverse=True)

    for c in sorted_candidates:
        score = float(c.get("final_score", 0.0) or 0.0)
        metadata = normalize_v2_metadata(c.get("metadata", {}) or {})
        applicability = c.get("applicability", {}) or {}
        decision = applicability.get("decision", "pass")
        max_role = applicability.get("max_role", "primary")
        strength = safe_text(metadata.get("evidence_strength")).lower()

        if decision != "pass":
            rejected.append({
                "id": c.get("id"),
                "support_type": "not_applicable",
                "reason": "工程适用性过滤未通过。",
            })
            continue

        # background 绝对不进入 selected
        if strength == "background":
            rejected.append({
                "id": c.get("id"),
                "support_type": "background",
                "reason": "证据强度为 background，规则禁止进入 selected。",
            })
            continue

        if score >= 0.65 and len(selected) < max_selected:
            if strength == "direct" and max_role == "primary":
                support_type = "direct"
                relevance = "high"
            elif strength in {"direct", "indirect"} or max_role in {"primary", "supporting"}:
                support_type = "indirect"
                relevance = "medium"
            else:
                support_type = "background"
                relevance = "low"

            # background 证据只有在没有更好选择时才保留
            if support_type == "background" and len(selected) > 0:
                rejected.append({
                    "id": c.get("id"),
                    "support_type": "background",
                    "reason": "证据为背景信息，已有更好证据，不再保留。",
                })
                continue

            selected.append({
                "id": c.get("id"),
                "support_type": support_type,
                "evidence_role": "supporting" if max_role != "primary" else "primary",
                "relevance": relevance,
                "reason": f"未启用 LLM 审查。按 V2 元数据（strength={strength}，score={score:.3f}）保留。",
            })
        else:
            rejected.append({
                "id": c.get("id"),
                "support_type": "not_applicable",
                "reason": f"分数不足（{score:.3f} < 0.65）或超出最大数量（{max_selected}）。",
            })

    return {"selected": selected, "rejected": rejected, "judge_method": "fallback"}


def apply_judge(
    candidates: list[dict[str, Any]],
    judge_result: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {c.get("id"): c for c in candidates}
    selected_items = []
    rejected_items = []

    for j in judge_result.get("selected", []) or []:
        eid = safe_text(j.get("id"))
        if eid not in by_id:
            continue
        item = dict(by_id[eid])
        item["llm_judge"] = j
        selected_items.append(item)

    # 将 judge 中 rejected 的也标注
    judged_ids = {safe_text(j.get("id")) for j in judge_result.get("selected", []) or []}
    for j in judge_result.get("rejected", []) or []:
        eid = safe_text(j.get("id"))
        if eid not in by_id or eid in judged_ids:
            continue
        item = dict(by_id[eid])
        item["llm_judge"] = j
        rejected_items.append(item)

    # 未被 judge 涉及的候选（可能 judge 截断了）也标为 rejected
    all_judged = judged_ids | {safe_text(j.get("id")) for j in judge_result.get("rejected", []) or []}
    for c in candidates:
        eid = safe_text(c.get("id"))
        if eid and eid not in all_judged:
            item = dict(c)
            item["llm_judge"] = {
                "id": eid,
                "support_type": "not_applicable",
                "reason": "未被 LLM 审查涵盖（候选数超出限制）。",
            }
            rejected_items.append(item)

    return selected_items, rejected_items
