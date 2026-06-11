from __future__ import annotations

import logging

from cooling_rag_mg.json_utils import loads_lenient

_log = logging.getLogger(__name__)

_EXTRACT_PROMPT = (
    "你是船舶工程参数提取专家。\n"
    "从以下证据文本中提取所有明确的量化参数值（数值+单位）。\n\n"
    "证据文本：\n{text}\n\n"
    "要求：\n"
    "1. 只提取文本中明确出现的数值，不得推断或补充\n"
    "2. 每个参数包含：value_text（原文表述）、operator（<=/>=/</>/=，无比较符时用空字符串\"\"）、unit（单位）\n"
    "3. 若无任何量化参数，返回空列表\n\n"
    '以 JSON 格式返回，格式：{{"values": [{{"value_text": "...", "operator": "...", "unit": "..."}}]}}'
)


def extract_values_from_evidence(text: str, client, model: str) -> list[dict]:
    """从单条 evidence unit 文本提取量化参数值列表。无文本或出错返回空列表。"""
    if not text or not text.strip():
        return []
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _EXTRACT_PROMPT.format(text=text[:800])}],
            temperature=0,
            max_tokens=400,
        )
        data = loads_lenient(resp.choices[0].message.content)
        if not data and resp.choices[0].message.content.strip():
            _log.warning("extract_values_from_evidence: failed to parse LLM response")
        values = data.get("values", [])
        return values if isinstance(values, list) else []
    except Exception as exc:
        _log.warning("extract_values_from_evidence failed: %s", exc)
        return []


def annotate_evidence_units(evidence_units: list[dict], client, model: str) -> list[dict]:
    """对证据单元列表做值提取标注，返回带 _extracted_values / _has_quantitative 的副本。"""
    result = []
    for eu in evidence_units:
        eu_copy = dict(eu)
        values = extract_values_from_evidence(eu.get("text", ""), client, model)
        eu_copy["_extracted_values"] = values
        eu_copy["_has_quantitative"] = len(values) > 0
        result.append(eu_copy)
    return result
