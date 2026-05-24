# -*- coding: utf-8 -*-
"""
Generate diverse raw stakeholder requirements for experimental evaluation.

Covers 6 stakeholder types × multiple requirement types = 20 test requirements.
Output is a JSONL file compatible with the pipeline's input format.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import safe_text

# ─────────────────────────────────────────────
# 生成矩阵：利益相关方 × 需求类型 × 数量
# ─────────────────────────────────────────────
_MATRIX: list[dict[str, Any]] = [
    {
        "stakeholder": "船东代表",
        "code": "OWN",
        "types": ["reliability", "redundancy", "operation", "safety_environment"],
        "count": 4,
        "perspective": (
            "关注系统整体运行可靠性、冗余备用能力、各工况稳定性和安全风险，"
            "表达通常较宏观，偏重航行安全和运营成本。"
        ),
    },
    {
        "stakeholder": "主机厂家",
        "code": "MFR",
        "types": ["parameter", "control", "alarm_protection"],
        "count": 4,
        "perspective": (
            "关注接口参数、温度/压力/流量限值、控制逻辑和报警保护，"
            "表达较技术性，有时引用厂家技术手册规定。"
        ),
    },
    {
        "stakeholder": "系统设计方",
        "code": "SYS",
        "types": ["configuration", "verification"],
        "count": 3,
        "perspective": (
            "关注系统回路配置、原理图完整性、计算书和船级社审图需求，"
            "表达偏向工程文件和设计标准。"
        ),
    },
    {
        "stakeholder": "船厂建造方",
        "code": "SHY",
        "types": ["installation", "maintainability"],
        "count": 3,
        "perspective": (
            "关注管路施工、安装空间、冲洗试压程序和后续维护便利性，"
            "表达偏向现场操作和施工规范。"
        ),
    },
    {
        "stakeholder": "设备采购方",
        "code": "PRO",
        "types": ["configuration", "parameter", "safety_environment"],
        "count": 3,
        "perspective": (
            "关注设备选型依据、接口标准、材料要求和环保合规，"
            "表达偏向设备规格书和采购技术要求。"
        ),
    },
    {
        "stakeholder": "船级社",
        "code": "CLS",
        "types": ["verification", "alarm_protection"],
        "count": 3,
        "perspective": (
            "关注规范符合性验证、图纸审查、报警和保护系统的规范要求，"
            "表达偏向规则条款和发证要求。"
        ),
    },
]

_GENERATOR_PROMPT = """\
你是船舶主机冷却水系统需求专家。

任务：模拟"{stakeholder}"的视角，生成 {count} 条原始利益相关方需求。

## 利益相关方视角
{perspective}

## 需求类型覆盖
每条需求应属于以下类型之一（每条只选一个）：{types}

## 证据库部件和关注点摘要（供参考）
{evidence_summary}

## 生成规则
1. 每条需求用自然语言写，模拟真实利益相关方的表达方式（允许口语化、模糊、一句话涵盖多个方面）
2. 长度 60-150 字，不要太精炼，保留原始需求的不确定性
3. 不同条需求覆盖不同工程关注点，不重复
4. 不要输出工程化需求（不要写 shall/应…），写原始诉求

## 输出格式（合法 JSON，不输出 Markdown）
{{
  "requirements": [
    {{
      "requirement_id": "{code}-01",
      "stakeholder": "{stakeholder}",
      "intended_type": "reliability",
      "requirement_text": "..."
    }}
  ]
}}
"""


def _build_evidence_summary(evidence_units_path: str | Path, max_items: int = 40) -> str:
    """从 evidence_units.jsonl 提取部件和关注点摘要，用于提示词。"""
    try:
        units = read_jsonl(str(evidence_units_path))
    except Exception:
        return "（无法读取 evidence_units，摘要省略）"

    lines: list[str] = []
    for u in units[:max_items]:
        meta = normalize_v2_metadata(u.get("metadata", {}))
        topic = safe_text(meta.get("topic"))
        comps = "、".join(meta.get("component_objects", [])[:3])
        aspects = "、".join(meta.get("requirement_intents", [])[:3])
        if topic:
            lines.append(f"- {topic}（部件：{comps}；方面：{aspects}）")

    return "\n".join(lines[:25]) if lines else "（摘要为空）"


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    for prefix in ("```json", "```"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
    raise ValueError("Response is not valid JSON")


def generate_test_requirements(
    evidence_units_path: str | Path,
    output_path: str | Path,
    *,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    """
    Generate 20 diverse raw stakeholder requirements for experimental evaluation.

    Args:
        evidence_units_path: Path to evidence_units.jsonl (used to build summary prompt).
        output_path:         Destination JSONL file.
        overwrite:           If False and file exists, load and return existing data.

    Returns:
        List of requirement dicts compatible with pipeline input.
    """
    out = Path(output_path)
    if out.exists() and not overwrite:
        print(f"[Generator] Loading existing test requirements from {out}")
        return read_jsonl(str(out))

    cfg = get_config()
    if not cfg.deepseek.enabled:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is required to generate test requirements. "
            "Set it in .env and restart."
        )

    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
    evidence_summary = _build_evidence_summary(evidence_units_path)
    all_requirements: list[dict[str, Any]] = []

    for entry in _MATRIX:
        stakeholder = entry["stakeholder"]
        code = entry["code"]
        count = entry["count"]
        types_str = "、".join(entry["types"])

        prompt = _GENERATOR_PROMPT.format(
            stakeholder=stakeholder,
            code=code,
            count=count,
            perspective=entry["perspective"],
            types=types_str,
            evidence_summary=evidence_summary,
        )

        try:
            resp = client.chat.completions.create(
                model=cfg.deepseek.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.75,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            obj = _extract_json(resp.choices[0].message.content or "{}")
            reqs: list[dict[str, Any]] = obj.get("requirements", [])

            # 重新编号，保证全局唯一
            offset = len(all_requirements)
            for i, r in enumerate(reqs, start=1):
                r["requirement_id"] = f"{code}-{offset + i:02d}"
                r.setdefault("stakeholder", stakeholder)

            all_requirements.extend(reqs)
            print(f"[Generator] {stakeholder}: generated {len(reqs)} requirement(s)")

        except Exception as exc:
            print(f"[Generator] {stakeholder}: failed — {exc}")

    write_jsonl(str(out), all_requirements)
    print(f"[Generator] Saved {len(all_requirements)} requirements → {out}")
    return all_requirements
