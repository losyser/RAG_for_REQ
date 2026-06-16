"""
requirement_analyzer.py

Given a raw requirement text, extract the relevant (component, intent) pairs
from the evidence taxonomy so that retrieval can be pre-filtered to only
the evidence units that are actually relevant.

Example
-------
Input:  "膨胀水箱液位需能直观显示并具备自动补水功能"
Output: [("expansion_tank", "level_control"),
         ("expansion_tank", "alarm_setpoint"),
         ("expansion_tank", "makeup_water")]
"""
from __future__ import annotations

import json
from typing import Any

from cooling_rag_mg.evidence_taxonomy import (
    COMPONENTS, INTENTS, TAXONOMY, valid_pair,
)
from cooling_rag_mg.json_utils import loads_lenient

# ── Taxonomy description for the LLM prompt ──────────────────────────────────

def _taxonomy_block() -> str:
    lines: list[str] = []
    for comp, intents in TAXONOMY.items():
        cdesc = COMPONENTS.get(comp, "")
        intent_strs = ", ".join(
            f"{i}（{INTENTS.get(i,'')[:18]}）" for i in intents
        )
        lines.append(f"  {comp}（{cdesc}）: [{intent_strs}]")
    return "\n".join(lines)

_TAXONOMY_BLOCK = _taxonomy_block()   # built once at import time

_SYSTEM = """你是船舶主机冷却水系统需求工程专家。
给定一条原始需求，从以下 Taxonomy 中找出所有**直接相关**的（部件，工程方面）对。

规则：
- 只选与需求文本明确相关的对，不要过度扩展
- 每对都必须来自下方 Taxonomy（不能自造）
- 一条需求通常对应 1-4 个对；若需求较宽泛可适当多选
- 输出 JSON 列表，每项含 component 和 intent 两个字段

Taxonomy（部件: [可选方面]）：
{taxonomy}"""

_USER = """原始需求：{requirement}

请列出所有直接相关的（component, intent）对。
只输出 JSON 数组，例如：
[
  {{"component": "expansion_tank", "intent": "level_control"}},
  {{"component": "expansion_tank", "intent": "alarm_setpoint"}}
]"""


# ── Core functions ────────────────────────────────────────────────────────────

def build_prompt(requirement_text: str) -> list[dict]:
    return [
        {"role": "system", "content": _SYSTEM.format(taxonomy=_TAXONOMY_BLOCK)},
        {"role": "user",   "content": _USER.format(requirement=requirement_text)},
    ]


def parse_pairs(raw: str) -> list[tuple[str, str]]:
    """Parse LLM output → list of valid (component, intent) tuples.

    Handles both plain arrays and dict wrappers, and strips markdown fences.
    """
    import re
    text = (raw or "").strip()
    # strip ```json ... ``` fences
    text = re.sub(r"^```[a-z]*\n?", "", text).rstrip("`").strip()
    try:
        obj = json.loads(text)
    except Exception:
        # fallback: try to find first [...] or {...} block
        m = re.search(r"(\[.*?\]|\{.*?\})", text, re.DOTALL)
        if not m:
            return []
        try:
            obj = json.loads(m.group(1))
        except Exception:
            return []
    # handle dict wrapping: {"pairs": [...]}
    if isinstance(obj, dict):
        obj = obj.get("pairs", obj.get("results", []))
    if not isinstance(obj, list):
        return []

    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in obj:
        if not isinstance(item, dict):
            continue
        comp   = str(item.get("component", "")).strip()
        intent = str(item.get("intent",    "")).strip()
        pair   = (comp, intent)
        if pair not in seen and valid_pair(comp, intent):
            out.append(pair)
            seen.add(pair)
    return out


def analyze_requirement(
    requirement_text: str,
    client: Any,
    model: str,
    temperature: float = 0.0,
) -> list[tuple[str, str]]:
    """Call LLM and return validated (component, intent) pairs.

    Returns an empty list if the LLM is unavailable or returns nothing valid.
    The caller should fall back to unfiltered retrieval in that case.
    """
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=build_prompt(requirement_text),
            temperature=temperature,
            max_tokens=400,
        )
        raw = resp.choices[0].message.content or "[]"
    except Exception:
        return []
    return parse_pairs(raw)


def components_and_intents(
    pairs: list[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    """Split pairs into separate component and intent lists for filter calls."""
    comps   = list(dict.fromkeys(c for c, _ in pairs))
    intents = list(dict.fromkeys(i for _, i in pairs))
    return comps, intents
