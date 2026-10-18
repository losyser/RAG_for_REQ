# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import copy
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from openai import OpenAI

from cooling_rag_mg.config import get_config
from cooling_rag_mg.llm_cache import cached_completion
from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import safe_text, truncate
from cooling_rag_mg.ui_evidence_contracts import retain_ui_evidence, prepare_ui_output, finish_ui_audit, bounded_ui_excerpt

try:
    from langgraph.graph import END, StateGraph
except Exception as exc:  # pragma: no cover
    END = None
    StateGraph = None
    LANGGRAPH_IMPORT_ERROR = exc
else:
    LANGGRAPH_IMPORT_ERROR = None


# ─────────────────────────────────────────────
# 核心 prompt：大幅改进
# ─────────────────────────────────────────────
ENGINEERING_REQUIREMENT_PROMPT = """
你是船舶主机冷却水系统高级需求工程师。
任务：基于原始利益相关方需求和已审查的证据，生成可直接用于工程设计、建造、调试和验收的正式需求文件。

## 输入结构
- original_requirement：原始利益相关方需求
- retrieval_context.supported_evidence：已通过审查的 direct/indirect 证据（按主题分组）
- retrieval_context.background_evidence_for_reference_only：背景证据（仅参考）
- retrieval_context.evidence_gap_summary：证据缺口

---

## 【F】范围约束（最高优先级，凌驾于其他所有规则）

### F1 允许方面列表
输入中 retrieval_context.allowed_engineering_aspects 列出了本次可以生成工程需求的全部工程方面。
每条方面包含：
- topic：方面名称
- source_phrase：原始需求中支撑该方面的词句
- implication_type：explicit（原文明确）或 direct_implication（工程直接隐含）

### F2 生成规则
- engineering_requirements 必须且只能覆盖 allowed_engineering_aspects 中列出的方面
- 每条 engineering_requirement 的 topic 字段必须与 allowed_engineering_aspects 中的
  topic 值完全一致（逐字复用，不得改写），以便系统自动范围校验
- 每条 engineering_requirement 在 engineering_rationale 中必须写明：
  "本条覆盖方面【topic】，来自原始需求「source_phrase」"
- 若有证据涉及 allowed_engineering_aspects 之外的方面，将其记录在 evidence_gaps，
  不得生成对应的 engineering_requirements 条目
- 若 allowed_engineering_aspects 为空列表，则按原始需求文本本身的结构生成，不受此约束

### F3 禁止行为
✗ 添加 allowed_engineering_aspects 中未列出的任何工程方面
✗ 以"工程完整性"或"证据支撑"为由扩展范围
✗ 将 evidence_gaps 中的信息转化为 engineering_requirements 条目

---

## 【A】数值安全规则（最高优先级，违反即输出无效）

### A1 数值来源三档
| 数值来源 | 允许写法 |
|---|---|
| 证据原文中明确给出 | 可写入，并在 engineering_rationale 注明"来自证据 E-XXX-XXX 原文" |
| 证据提及但需厂家确认 | 写为"按主机厂家 Technical Data 确认" |
| 证据未提及，模型自行推断 | **严格禁止**，必须用下表占位表述替换 |

### A2 标准占位表述（逐字使用，不得改写）
- 参数限值（温度、压力、流量）→ 按主机厂家 Technical Data 确认
- 试验工况和时长 → 按项目调试大纲或厂家试验程序确认
- 记录频率 → 按调试大纲要求
- 显示/测量精度 → 满足监控系统设计规格书要求
- 设计海水温度 → 按项目设计基准（Design Basis）确认

### A3 support_status 与数值的对应关系
- need_confirmation 或 supported_by_indirect_evidence：acceptance_criteria 中**一律不得出现**温度值、压力值、百分比、时长、频率、精度等具体数字，全部用 A2 占位表述。
- verified_by_direct_evidence：可写数值，但 engineering_rationale 必须写"数值来自证据 [E-XXX] 原文"。
- evidence_gap：shall_statement 和 acceptance_criteria 中**禁止出现**任何具体数值，全部使用 A2 占位表述或"待补充相关工程证据后确认"。

### A4 多厂家参数禁止合并
不同厂家/机型的参数值（如 MAN 49/60DF 的 3%、Caterpillar 的 15%、某型的 96 kPa）**禁止并列写入同一条需求**。
正确写法：膨胀水箱容量应按实际选定主机厂家 Technical Data 确认，不同厂家和机型限值不同，不得直接套用其他厂家数据。
禁止写法：膨胀水箱容量不低于 3%（或 15%），设计压力不低于 96 kPa。

---

## 【B】shall_statement 格式规范

### B1 格式模板
[主语：系统/部件] 应/不应 [动词：配置/设置/满足/保证] [宾语：具体对象或条件]，[工况限定（如适用）]。

### B2 合格示例
✓ 主机冷却水系统应配置不少于两台冷却水泵，一用一备，单台泵发生故障时系统应能维持主机基本运行。
✓ 冷却水泵出口管路应设置压力传感器，测量信号应接入集控室监控系统并具备超低压报警功能。
✓ 系统管路布置应便于现场施工，法兰连接处应留有不少于满足拆装工具操作所需的检修空间，具体尺寸按船级社规范和厂家安装手册确认。

### B3 禁止写法（以下写法一律不合格）
✗ 主机冷却水系统应保持稳定运行。（无动词、无对象、无条件）
✗ 系统应具备较高可靠性。（不可验证）
✗ 冷却水参数应满足要求。（"要求"指代不明）
✗ 系统调试期间运行 4 小时。（数值无证据来源）

---

## 【C】结构规则

### C1 只能使用 supported_evidence
禁止使用 background_evidence 生成工程需求。evidence_gap_summary 只能进入 evidence_gaps 字段。

### C2 完整性原则
- engineering_requirements 列表必须涵盖原始需求的**所有工程方面**，不得因缺少证据而省略条目。
- 无直接或间接证据支撑的条目，仍应出现在 engineering_requirements 中，support_status 设为 evidence_gap，
  shall_statement 基于原始需求文本或 evidence_gap_summary 中的 sub_text 整理（不得编造参数），
  acceptance_criteria 只写"待补充相关工程证据后方可确认验收判据"。
- evidence_gaps 字段用于补充说明哪些方面缺少证据及建议的补充方向，与 engineering_requirements 中的
  evidence_gap 条目形成对应关系。

### C3 层级结构
- level=1：工程主题（如"冷却水泵冗余配置"、"管路布置与施工"）
- level=2：该主题下的具体 shall 语句
- 同主题需求必须归并，不得全部展平为 level=1

### C4 installation 类归并方式
管路布置、支架固定、冲洗程序、压力试验、设备接口 各为一个 level=1，下设 level=2 细节，不要把每个部件的安装要求拆成独立 level=1。

### C5 证据缺口子需求的处理
输入中 evidence_gap_summary 的每一条包含了检索阶段未找到证据的子需求原文（sub_text）和类型（sub_requirement_type）。
必须为每一条 evidence_gap_summary 生成对应的 engineering_requirements 条目：
- support_status = evidence_gap
- shall_statement 基于 sub_text 原文整理，语言转为 shall 句式，不添加未经证实的参数
- evidence_ids 为空列表
- acceptance_criteria 只写"待补充相关工程证据后方可确认验收判据"

**去重规则**：若 evidence_gap 子需求的核心语义与已有 engineering_requirement 条目高度重叠
（同一主题、同一部件、同一工况），则将其**合并**到已有条目，将已有条目的 support_status
降为 evidence_gap，不要另建新条目。只有语义明显不同的缺口才单独新建。

---

## 【D】证据追溯规则

### D1 evidence_ids 精选原则
每条需求最多 5 个 evidence_ids，只保留直接支撑该条 shall_statement 的证据。
engineering_rationale 必须说明每个证据 ID 支撑了 shall 的哪个具体方面，格式：
"E-XXX-001 支撑了[XXX方面]；E-YYY-002 支撑了[YYY方面]。"

### D2 support_status 判断标准
- verified_by_direct_evidence：至少 1 条 direct 证据原文直接给出参数限值、规则义务或试验步骤
- supported_by_indirect_evidence：有相关证据但缺具体判据，需结合其他文件
- need_confirmation：有证据但必须厂家确认技术数据后才能定值
- evidence_gap：无有效证据支撑——此状态的条目必须出现在 engineering_requirements 中，shall_statement 基于原始需求整理，acceptance_criteria 写"待补充相关工程证据后方可确认"

### D3 适用性约束
证据来自特定厂家/机型时，applicability_constraints 必须写明限制。
格式："本条需求基于 [厂家/机型] 证据，适用范围限于 [限定条件]，其他厂家和机型应按各自 Technical Data 另行确认。"

### D4 结构化约束字段的使用（最高优先级）
部分证据条目附带 `constraint` 字段，包含从规范原文提取的结构化信息。当证据存在 `constraint` 字段时：
- `constraint.核心要求` 即为规范原文确定的 shall 核心语句，**必须直接使用**（而不是从冗长的 text 中自行提炼）
- `constraint.可接受标准` 若非 null，**必须原文引用**到 acceptance_criteria 中
- `constraint.验证方式` 若非 null，**必须作为 verification_method 的依据**
- `constraint.规范依据` 若非 null，**必须写入 engineering_rationale**（格式："依据 [规范依据]"）
- `constraint.强制级别` 为"强制"时，support_status 不得低于 supported_by_indirect_evidence

这些字段经过规范原文提取校验，优先级高于从 text 字段自行推断。

---

## 【E】verification_method 选择
- review：图纸、文件、设计符合性审查
- inspection：现场目视检查、安装检查
- calculation：热平衡、流量、压降计算
- test：台架试验、系统功能试验
- commissioning_check：调试期间验证
- operation_check：运行状态检查
- maintenance_check：维护状态检查
- class_approval：船级社审批/发证

---

## 输出格式（合法 JSON，不输出 Markdown，不输出注释）
{
  "requirement_set_id": "ER-R001",
  "source_requirement_id": "R001",
  "stakeholder": "船东代表",
  "generation_basis": "original_requirement_and_supported_evidence_only",
  "professional_summary": "覆盖主机冷却水系统可靠性要求，包含冷却能力、冗余配置和工况适应性。",
  "assumptions": [],
  "engineering_requirements": [
    {
      "id": "ER-R001-01",
      "parent_id": "ER-R001",
      "level": 1,
      "requirement_type": "redundancy",
      "topic": "冷却水泵冗余配置",
      "shall_statement": "主机冷却水系统应配置不少于两台冷却水泵，实现一用一备；任意单台泵发生故障时，系统应能通过备用泵维持主机在不低于规定最低功率下连续运行。",
      "engineering_rationale": "E-PUMP-RED-001（船级社规则）支撑了一用一备的配置义务；E-SYS-OP-003（系统设计指南）支撑了单台故障后的维持运行要求。",
      "acceptance_criteria": [
        "检查图纸确认泵的台数和备用切换回路配置符合本条要求。",
        "调试期间模拟主泵故障，确认备用泵自动启动并维持主机运行，具体功率限值和切换时间按项目调试大纲确认。"
      ],
      "verification_method": "commissioning_check",
      "evidence_ids": ["E-PUMP-RED-001", "E-SYS-OP-003"],
      "support_status": "verified_by_direct_evidence",
      "applicability_constraints": [],
      "risk_if_unmet": "单泵故障后无备用将导致主机停机，影响航行安全。"
    },
    {
      "id": "ER-R001-01-01",
      "parent_id": "ER-R001-01",
      "level": 2,
      "requirement_type": "parameter",
      "topic": "备用泵切换时间",
      "shall_statement": "主泵故障信号发出后，备用泵应在规定时间内完成自动启动并建立正常运行压力。",
      "engineering_rationale": "E-PUMP-RED-001 提及自动切换要求，但未给出具体时间限值，需厂家和项目确认。",
      "acceptance_criteria": [
        "按项目调试大纲或主机厂家试验程序确认备用泵启动响应时间，调试记录应包含切换时间实测值。"
      ],
      "verification_method": "commissioning_check",
      "evidence_ids": ["E-PUMP-RED-001"],
      "support_status": "need_confirmation",
      "applicability_constraints": ["具体切换时间限值按主机厂家 Technical Data 及项目调试大纲确认。"],
      "risk_if_unmet": "切换时间过长将导致主机冷却中断，触发过热保护。"
    }
  ],
  "relationships": [
    {
      "source": "R001",
      "target": "ER-R001-01",
      "type": "derive",
      "description": "由原始需求「冗余可靠性」和 E-PUMP-RED-001 直接证据派生。"
    },
    {
      "source": "ER-R001-01",
      "target": "ER-R001-01-01",
      "type": "refine",
      "description": "细化为切换时间的具体参数要求。"
    }
  ],
  "evidence_gaps": [
    {
      "related_requirement_id": "ER-R001",
      "gap_type": "parameter_source_gap",
      "description": "缺少主机厂家 Technical Data 中的备用泵切换时间限值和主机最低维持功率要求。",
      "suggested_document_update": "补充主机厂家 Technical Data 和项目调试大纲。"
    }
  ],
  "confirmation_items": [
    {
      "item": "确认主机在单泵运行时允许的最低持续功率。",
      "reason": "现有证据仅说明需维持基本运行，未给出功率下限数值，需厂家 Technical Data 确认。"
    }
  ]
}
"""

JSON_REPAIR_PROMPT = """
你是 JSON 修复器。把用户提供的内容修复为合法 JSON。
只输出合法 JSON，不要输出解释，不要输出 Markdown。
不得增删业务字段含义，只修复格式问题。
"""


UI_MAX_PROMPT_CHARS = int(os.getenv("UI_MAX_PROMPT_CHARS", "96000"))


class RequirementAgentState(TypedDict, total=False):
    generation_blocked: str
    requirement: dict[str, Any]
    retrieval_context: dict[str, Any]
    compact_context: dict[str, Any]
    llm_raw: str
    output: dict[str, Any]
    errors: list[str]


def extract_json(text: str) -> dict[str, Any]:
    text = safe_text(text)
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.I).strip()
    text = re.sub(r"```$", "", text).strip()
    text = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = re.sub(r",\s*([}\]])", r"\1", text[start: end + 1])
        return json.loads(candidate)
    raise ValueError("LLM 返回不是合法 JSON")


def repair_json_with_deepseek(raw_text: str) -> dict[str, Any]:
    cfg = get_config()
    if not cfg.deepseek.enabled:
        raise RuntimeError("DeepSeek 未配置，无法修复 JSON。")
    client = cfg.deepseek.make_client()
    resp = cached_completion(
        client,
        model=cfg.deepseek.model,
        messages=[
            {"role": "system", "content": JSON_REPAIR_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        temperature=0,
        max_tokens=cfg.deepseek.max_tokens_requirement_agent,
        response_format={"type": "json_object"},
    )
    return extract_json(resp.choices[0].message.content or "{}")


def collect_requirement_context(payload: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    for req in payload.get("requirements", []) or []:
        if safe_text(req.get("requirement_id")) == safe_text(requirement_id):
            return req
    return {}


def compact_evidence(ev: dict[str, Any], text_limit: int = 600) -> dict[str, Any]:
    """构建送给工程需求 agent 的证据摘要，保留关键约束字段。
    
    text_limit 可由调用方根据 gap 数量动态缩减，避免 token 超限。
    """
    meta = normalize_v2_metadata(ev.get("metadata", {}) or {})
    judge = ev.get("llm_judge", {}) or {}

    # 关键约束字段完整保留（最多 250 字）
    unsupported = safe_text(meta.get("unsupported_requirements"))
    if len(unsupported) > 250:
        unsupported = unsupported[:250] + "…"
    summary = safe_text(meta.get("normalized_summary"))
    if len(summary) > 250:
        summary = summary[:250] + "…"

    out = {
        "id": ev.get("id"),
        "support_type": judge.get("support_type", ""),
        "evidence_role": judge.get("evidence_role", ""),
        "judge_reason": judge.get("reason", ""),
        # 证据文本按调用方指定长度截断
        "text": truncate(ev.get("text", ""), text_limit),
        # 关键元数据
        "topic": meta.get("topic", ""),
        "source_document": meta.get("source_document", ""),
        "source_type": meta.get("source_type", ""),
        "location": meta.get("location", ""),
        "evidence_strength": meta.get("evidence_strength", ""),
        "is_generalizable": meta.get("is_generalizable", ""),
        "applicability_level": meta.get("applicability_level", ""),
        "manufacturer": meta.get("manufacturer", ""),
        "engine_model": meta.get("engine_model", ""),
        "system_type": meta.get("system_type", []),
        "component_objects": meta.get("component_objects", []),
        "requirement_intents": meta.get("requirement_intents", []),
        "engineering_phase": meta.get("engineering_phase", []),
        "applicable_condition": meta.get("applicable_condition", []),
        "can_support": meta.get("can_support", []),
        "limitation": meta.get("limitation", ""),
        "normalized_summary": summary,
        "supportable_requirements": meta.get("supportable_requirements", []),
        "unsupported_requirements": unsupported,
    }

    # Inject L1 structured constraint fields when available (v2 KB).
    # These provide the LLM with precise regulatory clause, mandatory level,
    # acceptance criteria and verification method — directly improving SHALL quality.
    constraint = ev.get("constraint") or {}
    if constraint.get("核心要求"):
        out["constraint"] = {k: v for k, v in constraint.items()
                             if k != "_extraction_meta" and v is not None}

    if "constraint" in out and len(json.dumps(out["constraint"], ensure_ascii=False)) > 1600:
        out["constraint"] = None
        out["_constraint_status"] = "omitted_over_budget"
    return retain_ui_evidence(out, ev, text_limit)


def _group_evidence_by_type(evidence_list: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    按证据的 requirement_intents 分组，帮助 agent 按主题归并。
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for ev in evidence_list:
        intents = ev.get("requirement_intents", []) or []
        key = intents[0] if intents else "general"
        groups.setdefault(key, []).append(ev)
    return groups


def compact_requirement_context(
    requirement_context: dict[str, Any],
    max_evidence: int = 20,
) -> dict[str, Any]:
    """
    构建送给工程需求 agent 的需求上下文。

    改进：
    1. 按 requirement_intents 分组展示证据，帮助 agent 按主题归并
    2. 保留子需求类型分布，帮助 agent 理解需求结构
    3. 根据子需求数量和 gap 数量动态缩短证据文本，防止 token 超限
    """
    supported: list[dict[str, Any]] = []
    background: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    support_ids: set[str] = set()
    sub_type_dist: dict[str, int] = {}
    sub_count = 0

    for sub in requirement_context.get("sub_requirements", []) or []:
        sub_count += 1
        rtype = sub.get("requirement_type", "other")
        sub_type_dist[rtype] = sub_type_dist.get(rtype, 0) + 1

        for ev in sub.get("selected_results", []) or []:
            judge = ev.get("llm_judge", {}) or {}
            stype = judge.get("support_type", "")
            # text_limit 先用占位符 0，后面统一设置
            item = compact_evidence(ev, text_limit=0)
            if stype in {"direct", "indirect"}:
                if item["id"] not in support_ids:
                    supported.append(item)
                    support_ids.add(item["id"])
            elif stype == "background":
                background.append(item)

        if sub.get("evidence_gap"):
            gap = dict(sub["evidence_gap"])
            gap["sub_requirement_id"] = sub.get("sub_requirement_id", "")
            gap["sub_topic"] = sub.get("topic", "")
            gap["sub_requirement_type"] = sub.get("requirement_type", "")
            gap["sub_text"] = sub.get("text", "")
            gaps.append(gap)

    if max_evidence < 1:
        raise ValueError("max_evidence must be positive")
    omitted_supported_ids = [e["id"] for e in supported[max_evidence:]]
    all_background_ids = list(dict.fromkeys(e["id"] for e in background if e.get("id")))
    supported = supported[:max_evidence]
    background = background[:6]

    # 动态文本截断：子需求多或 gap 多时缩短证据文本，防止 JSON 超限
    # 经验公式：基础 600 字，每多 1 个子需求减 20 字，每多 1 个 gap 减 30 字，下限 300 字
    text_limit = max(300, 600 - sub_count * 20 - len(gaps) * 30)
    for item in supported + background:
        raw_text = item.get("text", "")
        item.update(bounded_ui_excerpt(raw_text, text_limit))

    # 按 requirement_intents 分组（帮助 agent 归并）
    grouped_evidence = _group_evidence_by_type(supported)

    allowed_aspects = [
        {
            "topic": sub.get("topic", ""),
            "source_phrase": sub.get("source_phrase", ""),
            "implication_type": sub.get("implication_type", "explicit"),
        }
        for sub in requirement_context.get("sub_requirements", []) or []
        if sub.get("source_phrase")
    ]

    return {
        "requirement_id": requirement_context.get("requirement_id", ""),
        "stakeholder": requirement_context.get("stakeholder", ""),
        "raw_requirement_text": requirement_context.get("raw_requirement_text", ""),
        "generation_basis": "original_requirement_and_supported_evidence_only",
        "supported_evidence_by_topic": grouped_evidence,
        "supported_evidence": supported,
        "background_evidence_for_reference_only": background,
        # 用于 normalize_agent_output 的代码级 background 排除（CR-5 hard guard）
        "_background_evidence_ids": all_background_ids,
        "_omitted_supported_evidence_ids": omitted_supported_ids,
        "_evidence_order_policy": "first_selected_reference_not_recovered_rank",
        "evidence_gap_summary": gaps,
        "sub_requirement_type_distribution": sub_type_dist,
        "allowed_engineering_aspects": allowed_aspects,
        "sub_requirements_hidden_from_generation": True,
    }


def _sanitize_criteria(criteria: list[str]) -> list[str]:
    """
    清洗 need_confirmation / supported_by_indirect_evidence 状态下的验收判据。

    用正则检测常见"编造数值"模式并替换为标准占位表述：
    - 温度值：32°C、85°C 等
    - 压力值：0.3 MPa、96 kPa 等
    - 百分比：±5%、3% 等
    - 时长：4 小时、30 分钟 等
    - 频率：每 30 分钟记录 等
    - 精度：±1°C、±0.01 MPa 等

    检测到问题时在句尾追加说明，不强制删除原文（保留供人工复核），
    但在句前加上警告标记 [待确认数值]。
    """
    import re

    # 触发"编造数值"的正则模式
    _NUMBER_PATTERNS = [
        re.compile(r"\d+\s*°[Cc]"),                          # 温度值
        re.compile(r"\d+\.?\d*\s*(?:MPa|kPa|bar|psi)", re.I),  # 压力值
        re.compile(r"[±]\s*\d+\.?\d*\s*%"),                  # 百分比精度
        re.compile(r"\d+\.?\d*\s*%"),                         # 百分比
        re.compile(r"\d+\s*(?:小时|分钟|秒|h|min|s)\b"),     # 时长
        re.compile(r"每\s*\d+\s*(?:小时|分钟)"),              # 频率
        re.compile(r"[±]\s*\d+\.?\d*\s*°[Cc]"),              # 温度精度
        re.compile(r"[±]\s*\d+\.?\d*\s*(?:MPa|kPa)", re.I), # 压力精度
    ]

    sanitized = []
    for criterion in criteria:
        has_number = any(p.search(criterion) for p in _NUMBER_PATTERNS)
        if has_number:
            sanitized.append(f"[待确认数值] {criterion} → 上述数值需由证据原文、厂家 Technical Data 或项目文件确认后方可使用。")
        else:
            sanitized.append(criterion)
    return sanitized


def _collapse_orphan_intermediates(reqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove single-child intermediate nodes that carry no structural value.

    A node is an "orphan intermediate" when it is the only child of its parent
    AND itself has children.  Such nodes add no grouping value; their children
    are re-parented directly to the grandparent with the orphan's level.

    Processes only the topmost eligible orphan layer per iteration so that
    nested chains of orphans are unwound correctly one level at a time.
    """
    for _ in range(10):
        parent_to_children: dict[str, list[dict[str, Any]]] = {}
        for r in reqs:
            parent_to_children.setdefault(r.get("parent_id", ""), []).append(r)

        # Identify all candidates, then keep only those whose own parent is not
        # also a candidate (process top-down, one stratum per iteration).
        candidates: set[str] = set()
        for r in reqs:
            rid = r.get("id", "")
            pid = r.get("parent_id", "")
            siblings = [s for s in parent_to_children.get(pid, []) if s.get("id") != rid]
            own_children = parent_to_children.get(rid, [])
            if not siblings and own_children:
                candidates.add(rid)

        orphans = {rid for rid in candidates
                   if (next((r for r in reqs if r.get("id") == rid), {}) or {})
                      .get("parent_id", "") not in candidates}

        if not orphans:
            break

        reparent: dict[str, tuple[str, int]] = {}
        for r in reqs:
            if r.get("id", "") in orphans:
                pid = r.get("parent_id", "")
                level = int(r.get("level") or 1)
                for child in parent_to_children.get(r.get("id", ""), []):
                    reparent[child.get("id", "")] = (pid, level)

        new_reqs: list[dict[str, Any]] = []
        for r in reqs:
            rid = r.get("id", "")
            if rid in orphans:
                continue
            if rid in reparent:
                r = dict(r)
                r["parent_id"], r["level"] = reparent[rid]
            new_reqs.append(r)
        reqs = new_reqs

    return reqs


def normalize_agent_output(obj: dict[str, Any], requirement_id: str, *, evidence_scope: list[dict] | None = None, risk_policy: str = "legacy", quarantine_flags: list[dict] | None = None) -> dict[str, Any]:
    obj = prepare_ui_output(obj, requirement_id, evidence_scope)
    before_normalization = copy.deepcopy(obj)
    set_id = safe_text(obj.get("requirement_set_id")) or f"ER-{requirement_id}"
    obj["requirement_set_id"] = set_id
    obj["source_requirement_id"] = safe_text(obj.get("source_requirement_id")) or requirement_id
    obj["generation_basis"] = "original_requirement_and_supported_evidence_only"
    obj.setdefault("stakeholder", "")
    obj.setdefault("professional_summary", "")
    obj.setdefault("assumptions", [])
    obj.setdefault("engineering_requirements", [])
    obj.setdefault("relationships", [])
    obj.setdefault("evidence_gaps", [])
    obj.setdefault("confirmation_items", [])

    allowed_status = {
        "verified_by_direct_evidence",
        "supported_by_indirect_evidence",
        "need_confirmation",
        "evidence_gap",
    }
    allowed_verification = {
        "review", "inspection", "calculation", "simulation", "test",
        "commissioning_check", "operation_check", "maintenance_check", "class_approval",
    }

    cleaned_reqs: list[dict[str, Any]] = []
    for idx, req in enumerate(obj.get("engineering_requirements", []) or [], start=1):
        if not isinstance(req, dict):
            continue
        statement = safe_text(req.get("shall_statement"))
        if not statement:
            continue

        rid = safe_text(req.get("id")) or f"{set_id}-{idx:02d}"
        req["id"] = rid
        req["parent_id"] = safe_text(req.get("parent_id")) or set_id

        try:
            req["level"] = int(req.get("level") or 1)
        except Exception:
            req["level"] = 1

        req["acceptance_criteria"] = (
            req.get("acceptance_criteria")
            if isinstance(req.get("acceptance_criteria"), list)
            else []
        )

        req["evidence_ids"] = (
            req.get("evidence_ids")
            if isinstance(req.get("evidence_ids"), list)
            else []
        )

        # ── CR-5 hard guard: 强制剔除 background-strength evidence ids ──
        # 即使 LLM 违反 prompt 第 8 条把 background 证据放入 evidence_ids，
        # 这里也会在代码层把它们删掉，使"background 不进 selected_results"成为代码不变式。
        bg_ids = set(obj.get("_background_evidence_ids", []) or [])
        if bg_ids:
            before = len(req["evidence_ids"])
            req["evidence_ids"] = [eid for eid in req["evidence_ids"] if eid not in bg_ids]
            if before != len(req["evidence_ids"]):
                req.setdefault("applicability_constraints", [])
                req["applicability_constraints"].append(
                    f"代码层剔除了 {before - len(req['evidence_ids'])} 条 background-strength 证据引用。"
                )

        # support_status 校验
        if req.get("support_status") not in allowed_status:
            req["support_status"] = (
                "need_confirmation" if req["evidence_ids"] else "evidence_gap"
            )

        # verification_method 校验
        if req.get("verification_method") not in allowed_verification:
            req["verification_method"] = "review"

        # ── 后处理②：evidence_ids 裁剪上限为 5 ──
        if len(req["evidence_ids"]) > 5:
            req["evidence_ids"] = req["evidence_ids"][:5]
            if req.get("support_status") == "verified_by_direct_evidence":
                req["support_status"] = "need_confirmation"
            req.setdefault("applicability_constraints", [])
            req["applicability_constraints"].append(
                "证据 ID 已裁剪至前 5 条（primary 优先），完整证据列表见检索结果文件。"
            )

        # ── 后处理③：need_confirmation / indirect / evidence_gap 状态下清洗数值 ──
        unsafe_status = {
            "need_confirmation",
            "supported_by_indirect_evidence",
            "evidence_gap",
        }
        if req.get("support_status") in unsafe_status:
            req["acceptance_criteria"] = _sanitize_criteria(req["acceptance_criteria"])

        req["applicability_constraints"] = (
            req.get("applicability_constraints")
            if isinstance(req.get("applicability_constraints"), list)
            else []
        )

        req.setdefault("engineering_rationale", "")
        req.setdefault("risk_if_unmet", "")
        req.setdefault("requirement_type", "other")
        req.setdefault("topic", "")

        cleaned_reqs.append(req)

    # Collapse orphan intermediate nodes produced by the LLM
    collapsed = _collapse_orphan_intermediates(cleaned_reqs)
    removed_ids = {r.get("id") for r in cleaned_reqs} - {r.get("id") for r in collapsed}
    obj["engineering_requirements"] = collapsed

    # Drop relationships that reference a removed intermediate node
    if removed_ids:
        obj["relationships"] = [
            rel for rel in obj.get("relationships", []) or []
            if rel.get("source") not in removed_ids and rel.get("target") not in removed_ids
        ]

    # ── Scope validation: engineering_requirement topics must be in allowed_engineering_aspects ──
    allowed_topics = {
        a["topic"]
        for a in obj.get("allowed_engineering_aspects", []) or []
        if a.get("topic")
    }
    if allowed_topics:
        valid_reqs = []
        for req in obj["engineering_requirements"]:
            if req.get("topic", "") in allowed_topics:
                valid_reqs.append(req)
            else:
                obj.setdefault("evidence_gaps", []).append({
                    "related_requirement_id": req.get("id", ""),
                    "gap_type": "scope_violation",
                    "description": (
                        f"topic '{req.get('topic', '')}' 不在 allowed_engineering_aspects 列表中，"
                        "已从工程需求中移除。若确需覆盖该方面，请在原始需求中补充相应内容。"
                    ),
                    "suggested_document_update": "在原始需求中明确提及该工程方面。",
                })
        obj["engineering_requirements"] = valid_reqs

    obj["generated_at"] = datetime.now().isoformat(timespec="seconds")
    obj["agent"] = "langgraph_deepseek_engineering_requirement_agent"
    # 清理只用于内部 guard 的临时字段
    obj.pop("_background_evidence_ids", None)
    from cooling_rag_mg.generation_risks import annotate_generation_risks
    obj = finish_ui_audit(obj, before_normalization)
    obj["engineering_requirements"] = annotate_generation_risks(
        obj["engineering_requirements"], evidence_scope, policy=risk_policy)
    from cooling_rag_mg.evidence_quarantine import gate_ui_output
    return gate_ui_output(obj, quarantine_flags, evidence_scope=evidence_scope)


def build_graph(*, risk_policy: str = "legacy", quarantine_flags: list[dict] | None = None):
    from cooling_rag_mg.evidence_quarantine import active_flags, mask_prompt_evidence, gate_ui_output, PROMPT_RULE
    quarantined = active_flags(quarantine_flags)
    from cooling_rag_mg.generation_risks import annotate_generation_risks
    annotate_generation_risks([], None, policy=risk_policy)  # Validate before any client.

    def fallback_with_risks(state, errors):
        obj = build_fallback_output(state, errors)
        obj["engineering_requirements"] = annotate_generation_risks(
            obj["engineering_requirements"], (state.get("compact_context") or {}).get("supported_evidence"),
            policy=risk_policy)
        return gate_ui_output(obj, quarantine_flags, evidence_scope=(state.get('compact_context') or {}).get('supported_evidence'))
    if StateGraph is None or END is None:
        raise RuntimeError(
            "未安装 langgraph，无法运行需求工程智能体。请执行：pip install langgraph"
        ) from LANGGRAPH_IMPORT_ERROR

    def prepare_context(state: RequirementAgentState) -> RequirementAgentState:
        context = state.get("retrieval_context", {}) or {}
        compact = compact_requirement_context(context)
        compact = mask_prompt_evidence(compact, quarantine_flags)
        return {**state, "compact_context": compact, "errors": list(state.get("errors", []) or [])}

    def call_deepseek(state: RequirementAgentState) -> RequirementAgentState:
        cfg = get_config()
        if not cfg.deepseek.enabled:
            raise RuntimeError("DeepSeek 未配置 api_key，无法生成工程化需求。")
        payload = {
            "original_requirement": state.get("requirement", {}),
            "retrieval_context": state.get("compact_context", {}),
        }
        messages = [
            {"role": "system", "content": ENGINEERING_REQUIREMENT_PROMPT + "\n上下文状态partial_unknown、缺失条件、缺失型号均表示待确认，不能推断补齐。参数value_text/operator/unit须一起解释，省略内容不能当作不存在。原文片段及偏移仅供定位，不保证条件完整。原文偏移和字符预算不是工程参数，不得用于数值判据。support_status只是模型报告，不代表独立语义验证。"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
        if quarantined:
            messages[0]["content"] += PROMPT_RULE
        prompt_chars = sum(len(m["content"]) for m in messages)
        if UI_MAX_PROMPT_CHARS < 1 or prompt_chars > UI_MAX_PROMPT_CHARS:
            return {**state, "generation_blocked": f"prompt_budget_exceeded: {prompt_chars}/{UI_MAX_PROMPT_CHARS} characters"}
        client = cfg.deepseek.make_client()
        resp = cached_completion(
            client,
            model=cfg.deepseek.model,
            messages=messages,
            temperature=cfg.deepseek.temperature,
            max_tokens=cfg.deepseek.max_tokens_requirement_agent,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        return {**state, "llm_raw": raw}

    def parse_and_validate(state: RequirementAgentState) -> RequirementAgentState:
        requirement = state.get("requirement", {}) or {}
        requirement_id = safe_text(requirement.get("requirement_id"))
        errors = list(state.get("errors", []) or [])
        if state.get("generation_blocked"):
            errors.append(state["generation_blocked"])
            return {**state, "output": fallback_with_risks(state, errors), "errors": errors}

        try:
            obj = extract_json(state.get("llm_raw", "{}"))
        except Exception as exc:
            errors.append(f"工程化需求 JSON 解析失败，尝试修复：{exc}")
            try:
                obj = repair_json_with_deepseek(state.get("llm_raw", "{}"))
                errors.append("JSON 已通过 DeepSeek 修复。")
            except Exception as exc2:
                errors.append(f"JSON 修复失败：{exc2}")
                fallback = fallback_with_risks(state, errors)
                return {**state, "output": fallback, "errors": errors}

        try:
            # inject allowed_aspects from compact_context so normalize_agent_output can validate scope
            compact = state.get("compact_context", {}) or {}
            obj["allowed_engineering_aspects"] = compact.get("allowed_engineering_aspects", [])
            # inject background evidence ids so normalize_agent_output can strip them (CR-5 code guard)
            obj["_background_evidence_ids"] = list(compact.get("_background_evidence_ids", []) or [])

            obj = normalize_agent_output(obj, requirement_id, evidence_scope=compact.get("supported_evidence", []), risk_policy=risk_policy, quarantine_flags=quarantine_flags)
            if errors:
                obj.setdefault("assumptions", [])
                obj["assumptions"].extend(errors)
            return {**state, "output": obj, "errors": errors}
        except Exception as exc:
            errors.append(f"工程化需求结构校验失败：{exc}")
            fallback = fallback_with_risks(state, errors)
            return {**state, "output": fallback, "errors": errors}

    graph = StateGraph(RequirementAgentState)
    graph.add_node("prepare_context", prepare_context)
    graph.add_node("call_deepseek", call_deepseek)
    graph.add_node("parse_and_validate", parse_and_validate)
    graph.set_entry_point("prepare_context")
    graph.add_edge("prepare_context", "call_deepseek")
    graph.add_edge("call_deepseek", "parse_and_validate")
    graph.add_edge("parse_and_validate", END)
    return graph.compile()


def build_fallback_output(
    state: RequirementAgentState,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    requirement = state.get("requirement", {}) or {}
    context = state.get("compact_context", {}) or compact_requirement_context(
        state.get("retrieval_context", {}) or {}
    )
    rid = (
        safe_text(requirement.get("requirement_id"))
        or safe_text(context.get("requirement_id"))
        or "REQ"
    )
    set_id = f"ER-{rid}"
    supported = context.get("supported_evidence", []) or []
    gaps_in = context.get("evidence_gap_summary", []) or []

    engineering_reqs = []
    relationships = []

    if supported:
        direct_ids = [ev.get("id") for ev in supported if ev.get("support_type") == "direct"]
        indirect_ids = [ev.get("id") for ev in supported if ev.get("support_type") == "indirect"]
        status = "need_confirmation"
        if direct_ids:
            status = "need_confirmation"  # fallback 不能标为最终 verified
        elif indirect_ids:
            status = "supported_by_indirect_evidence"
        evidence_ids = direct_ids or indirect_ids

        er_id = f"{set_id}-01"
        engineering_reqs.append({
            "id": er_id,
            "parent_id": set_id,
            "level": 1,
            "requirement_type": requirement.get("requirement_type", "other"),
            "topic": "基于原始需求的保守工程化需求（需人工复核）",
            "shall_statement": safe_text(
                requirement.get("requirement_text") or context.get("raw_requirement_text")
            ),
            "engineering_rationale": "DeepSeek 输出失败。该条仅依据原始需求和已保留证据生成保守草案，需人工复核。",
            "acceptance_criteria": [
                "具体参数、验收判据和适用范围应由厂家技术数据、项目计算书、试验大纲或船级社文件确认。"
            ],
            "verification_method": "review",
            "evidence_ids": evidence_ids,
            "support_status": status,
            "applicability_constraints": ["fallback 结果不得直接作为最终工程指导级需求。"],
            "risk_if_unmet": "该要求未满足时可能影响冷却水系统工程适用性或运行可靠性。",
        })
        relationships.append({
            "source": rid,
            "target": er_id,
            "type": "derive",
            "description": "由原始需求和有支撑证据派生，需人工复核。",
        })

    gaps = []
    for gap in gaps_in:
        gaps.append({
            "related_requirement_id": set_id,
            "gap_type": gap.get("gap_type", "evidence_gap"),
            "description": gap.get("reason", "缺少直接证据。"),
            "suggested_document_update": gap.get("suggested_document_update", "补充直接工程证据。"),
        })

    return {
        "requirement_set_id": set_id,
        "source_requirement_id": rid,
        "stakeholder": requirement.get("stakeholder", context.get("stakeholder", "")),
        "generation_basis": "original_requirement_and_supported_evidence_only",
        "professional_summary": "基于检索结果生成的工程化需求草案，需人工复核。",
        "assumptions": errors or ["fallback 结果只用于保守展示，不作为最终工程指导依据。"],
        "engineering_requirements": engineering_reqs,
        "relationships": relationships,
        "evidence_gaps": gaps,
        "confirmation_items": [
            {"item": "需人工复核工程化需求表。", "reason": "大模型 JSON 输出失败或结构校验失败。"}
        ],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "agent": "fallback_engineering_requirement_agent",
        "generation_mode": "fallback",
        "_validation_report": {"version": "ui-structure-reference-v1", "mode": "fallback",
            "semantic_support": "unknown", "applicability": "unknown",
            "reference_scope": "supplied_support_context", "issues": list(errors or [])},
    }


def generate_engineering_requirements_for_requirement(
    requirement: dict[str, Any],
    retrieval_payload: dict[str, Any],
    *, risk_policy: str = "legacy", quarantine_flags: list[dict] | None = None,
) -> dict[str, Any]:
    requirement_id = safe_text(requirement.get("requirement_id"))
    context = collect_requirement_context(retrieval_payload, requirement_id)
    if not context:
        context = {
            "requirement_id": requirement_id,
            "stakeholder": requirement.get("stakeholder", ""),
            "raw_requirement_text": requirement.get("requirement_text", ""),
            "sub_requirements": [],
        }
    graph = build_graph() if risk_policy == "legacy" and not quarantine_flags else build_graph(risk_policy=risk_policy, quarantine_flags=quarantine_flags)
    result = graph.invoke({
        "requirement": requirement,
        "retrieval_context": context,
        "errors": [],
    })
    if result.get("output"):
        return result["output"]
    from cooling_rag_mg.evidence_quarantine import gate_ui_output
    return gate_ui_output(build_fallback_output(result), quarantine_flags, evidence_scope=(result.get('compact_context') or {}).get('supported_evidence'))


def generate_engineering_requirements(
    requirements: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
    *, risk_policy: str = "legacy", quarantine_flags: list[dict] | None = None,
) -> dict[str, Any]:
    outputs = [
        (generate_engineering_requirements_for_requirement(req, retrieval_payload) if risk_policy == "legacy" and not quarantine_flags
         else generate_engineering_requirements_for_requirement(req, retrieval_payload, risk_policy=risk_policy, quarantine_flags=quarantine_flags))
        for req in requirements
    ]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "agent": "langgraph_deepseek_engineering_requirement_agent",
        "requirement_sets": outputs,
    }


def save_engineering_requirements(
    root: str | Path,
    payload: dict[str, Any],
    create_subdir: bool = True,
) -> Path:
    root = Path(root)
    out_dir = (
        root / f"engineering_requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if create_subdir
        else root / "engineering_requirements"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "engineering_requirements.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_path = out_dir / "engineering_requirements.md"
    lines = ["# 工程化需求", ""]
    for req_set in payload.get("requirement_sets", []) or []:
        lines.append(
            f"## {req_set.get('requirement_set_id')}｜来源需求 {req_set.get('source_requirement_id')}｜{req_set.get('stakeholder','')}"
        )
        lines.append(f"> {req_set.get('professional_summary', '')}")
        lines.append("")

        if req_set.get("generation_mode") == "fallback":
            lines.append("> ⚠️ 注意：该组为 fallback 草案，需人工复核。")
            lines.append("")

        if req_set.get("assumptions"):
            lines.append("**前提说明**")
            for a in req_set["assumptions"]:
                lines.append(f"- {a}")
            lines.append("")

        lines.append("| ID | 层级 | 类型 | 主题 | 工程化需求 | 验证方式 | 支撑状态 | 证据 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for item in req_set.get("engineering_requirements", []) or []:
            evidence = ", ".join([safe_text(x) for x in item.get("evidence_ids", []) if safe_text(x)])
            statement = safe_text(item.get("shall_statement")).replace("|", "｜")
            lines.append(
                f"| {item.get('id','')} | L{item.get('level',1)} "
                f"| {item.get('requirement_type','')} | {item.get('topic','')} "
                f"| {statement} | {item.get('verification_method','')} "
                f"| {item.get('support_status','')} | {evidence} |"
            )
        lines.append("")

        # 验收判据展开
        lines.append("### 验收判据详情")
        for item in req_set.get("engineering_requirements", []) or []:
            criteria = item.get("acceptance_criteria", []) or []
            if criteria:
                lines.append(f"**{item.get('id','')} {item.get('topic','')}**")
                for c in criteria:
                    lines.append(f"- {c}")
        lines.append("")

        # 证据缺口
        gaps = req_set.get("evidence_gaps", []) or []
        if gaps:
            lines.append("### 证据缺口")
            for gap in gaps:
                lines.append(
                    f"- **{gap.get('related_requirement_id','')}** ｜ "
                    f"{gap.get('gap_type','')} ｜ {gap.get('description','')} ｜ "
                    f"建议：{gap.get('suggested_document_update','')}"
                )
            lines.append("")

        # 待确认项
        confirms = req_set.get("confirmation_items", []) or []
        if confirms:
            lines.append("### 待确认项")
            for ci in confirms:
                lines.append(f"- {ci.get('item','')} ｜ 原因：{ci.get('reason','')}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path
