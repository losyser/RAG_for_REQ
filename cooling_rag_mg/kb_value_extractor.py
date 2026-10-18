from __future__ import annotations

import os

import logging

from cooling_rag_mg.json_utils import loads_lenient
from cooling_rag_mg.evidence_contracts import validate_values, bounded_context

_log = logging.getLogger(__name__)

_EXTRACT_PROMPT = (
    "你是船舶工程参数提取专家。\n"
    "从以下证据文本中提取所有明确的量化参数值（数值+单位）。\n\n"
    "证据文本：\n{text}\n\n"
    "要求：\n"
    "1. 只提取文本中明确出现的数值，不得推断或补充\n"
    "2. 每个参数包含：value_text（原文表述）、operator（<=/>=/</>/=，无比较符时用空字符串\"\"）、unit（单位）\n"
    "3. 可选字段parameter、conditions、model、source_span均为字符串或null；source_span必须是证据原文的连续片段。缺失信息用null，不得推断\n"
    "4. 参数与适用条件须一起提取，不把文档编号、测点编号当作工程参数；若无参数返回空列表\n\n"
    '以 JSON 格式返回，格式：{{"values": [{{"value_text": "...", "operator": "...", "unit": "..."}}]}}'
)


def _parse_values_response(raw: str) -> list[dict] | None:
    """尝试从 LLM 响应中提取 values 列表；失败返回 None。"""
    import json, re
    if not raw:
        return None
    # 剥 markdown 围栏
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip(), flags=re.IGNORECASE)
    # 尝试标准 {"values": [...]} 格式
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            v = obj.get("values")
            return v if isinstance(v, list) else None
        if isinstance(obj, list):
            return obj  # LLM 直接返回列表
    except Exception:
        pass
    # 退路：抽取第一个 [...] 块
    start = text.find("[")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        return obj if isinstance(obj, list) else []
                    except Exception:
                        break
    # 退路：抽取第一个 {...} 块（兼容旧格式）
    data = loads_lenient(raw)
    if data:
        v = data.get("values")
        return v if isinstance(v, list) else None
    return None


def _extract_with_status(text: str, client, model: str) -> tuple[list[dict], str]:
    if not text or not text.strip():
        return [], "empty_input"
    context, omitted = bounded_context(text, int(os.getenv("RAG_EXTRACT_CHAR_LIMIT", "1200")))
    if not context:
        return [], "context_omitted_over_budget"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _EXTRACT_PROMPT.format(text=context)}],
            temperature=0,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        if getattr(resp.choices[0], "finish_reason", None) == "length":
            return [], "truncated_response"
        values = _parse_values_response(resp.choices[0].message.content)
        if values is None:
            return [], "parse_error"
        try:
            values = validate_values(values)
            for value in values:
                span = value.get("source_span")
                if span and span not in context:
                    raise ValueError("source_span is not verbatim in supplied context")
        except ValueError as exc:
            _log.warning("extract_values_from_evidence schema error: %s", exc)
            return [], "schema_error"
        status = "success" if values else "no_values"
        return values, status + ("_partial_context" if omitted else "")
    except Exception as exc:
        _log.warning("extract_values_from_evidence failed: %s", exc)
        return [], "api_error"


def extract_values_from_evidence(text: str, client, model: str) -> list[dict]:
    """Legacy list interface; annotation exposes failure status separately."""
    values, status = _extract_with_status(text, client, model)
    if status not in ("success", "no_values", "empty_input"):
        _log.warning("extract_values_from_evidence status=%s", status)
    return values


def annotate_evidence_units(evidence_units: list[dict], client, model: str) -> list[dict]:
    result = []
    for eu in evidence_units:
        eu_copy = dict(eu)
        values, status = _extract_with_status(eu.get("text", ""), client, model)
        eu_copy["_extracted_values"] = values
        eu_copy["_has_quantitative"] = bool(values)
        eu_copy["_extraction_status"] = status
        result.append(eu_copy)
    return result
