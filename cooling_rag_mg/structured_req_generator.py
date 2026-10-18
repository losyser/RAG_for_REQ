from __future__ import annotations

import logging
import os

from cooling_rag_mg.json_utils import loads_lenient
from cooling_rag_mg.evidence_contracts import (select_evidence, bounded_context, bounded_value_records, applicability_record, validate_shall)

_log = logging.getLogger(__name__)

_STRUCTURED_GEN_PROMPT = """你是船舶主机冷却水系统需求工程师，为 MBSE/SysML 建模生成结构化工程化 shall 需求。

## 原始需求
{source_requirement}

## 证据清单
{evidence_block}

## 输出要求
返回 JSON 格式：{{"shalls": [<shall对象>, ...]}}

每个 shall 对象包含：
- shall_statement：shall 语句（中文）
- measurable_criterion：可量化判据（见数值规则）
- applicable_condition：适用条件/工况
- verification_method：验证方式（检查/测试/分析）
- acceptance_criteria：验收准则列表
- evidence_citations：引用证据列表，每项含 kb_id/tier/source/has_clause

## 数值规则（最高优先级）
measurable_criterion 只有两种合法内容：
1. 来自上方证据清单中 [量化参数] 标注的具体值，需在 evidence_citations 中引用对应证据
2. {{{{TBD|unit:<单位>|ref:<来源文档>|component:<部件>|intent:<方面>|hint:<说明>}}}} 占位符

严禁写入证据清单中未出现的任何数字。所有字段使用中文。
参数的数值、运算符、单位、条件、型号和来源片段必须一起解释。null表示未记录，不能推断补齐。
适用性未知、条件缺失或记录因预算被省略时，不得将该参数泛化为项目限值；使用TBD并说明待确认内容。
证据中的异常数值、型号冲突或量纲冲突不能仅凭引用存在判为正确，应保留待核验说明。
"""

_NORAG_PROMPT = """你是船舶主机冷却水系统需求工程师，为 MBSE/SysML 建模生成结构化工程化 shall 需求。

## 原始需求
{source_requirement}

## 输出要求
返回 JSON 格式：{{"shalls": [<shall对象>, ...]}}

每个 shall 对象包含：
- shall_statement：shall 语句（中文）
- measurable_criterion：可量化判据（根据工程知识填写具体值，或填无法确定）
- applicable_condition：适用条件/工况
- verification_method：验证方式
- acceptance_criteria：验收准则列表
- evidence_citations：空列表 []

所有字段使用中文。
"""


_MAX_EVIDENCE_ITEMS = int(os.getenv("RAG_MAX_EVIDENCE_ITEMS", "12"))
_EU_TEXT_LIMIT = int(os.getenv("RAG_EU_TEXT_LIMIT", "500"))


def _build_evidence_block(annotated_evidence: list[dict]) -> str:
    """将标注后的证据单元格式化为 prompt 中的证据块文本。

    优先保留有量化参数的 EU；总数上限 _MAX_EVIDENCE_ITEMS，避免 prompt 过长。
    """
    ordered = select_evidence(annotated_evidence, _MAX_EVIDENCE_ITEMS)
    lines = []
    for eu in ordered:
        context, omitted = bounded_context(eu.get("text", ""), _EU_TEXT_LIMIT)
        values, omitted_values = bounded_value_records(eu.get("_extracted_values", []))
        source = str(eu.get("source_document") or "unknown")
        if len(source) > 300:
            source = "unknown (source label omitted_over_budget)"
        lines.append(f"[{eu['id']}] 层级:{eu.get('kb_tier', '?')} 来源:{source}")
        lines.append(f"  内容: {context or 'unknown (no complete paragraph fits)'}")
        lines.append(f"  [上下文省略段数] {omitted}")
        lines.append("  [上下文状态] " + ("partial_unknown: 存在省略，不能假定参数条件完整" if omitted else "all_paragraphs_retained: 仅表示文本未省略，不代表语义完整"))
        lines.append(f"  [抽取状态] {eu.get('_extraction_status', 'unknown_historical')}")
        lines.append(f"  [适用性记录] {applicability_record(eu)}")
        lines.append(f"  [量化参数] {values or 'none recorded'}")
        lines.append(f"  [完整参数省略条数] {omitted_values}")
        lines.append("  null=未记录；适用性仍需核实；引用等级不代表正确性。")
        lines.append("")
    return "\n".join(lines)


def _parse_shalls(raw: str) -> list[dict]:
    """从 LLM 响应中解析 shalls 列表。"""
    import json, re
    if not raw:
        return []
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip(), flags=re.IGNORECASE)
    # 标准格式 {"shalls": [...]}
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            shalls = obj.get("shalls", [])
        elif isinstance(obj, list):
            shalls = obj
        else:
            shalls = []
    except Exception:
        # 退路：抽取第一个 [...] 块
        shalls = []
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
                            shalls = json.loads(text[start:i + 1])
                        except Exception:
                            pass
                        break
        if not shalls:
            data = loads_lenient(raw)
            shalls = data.get("shalls", [])
    if not isinstance(shalls, list):
        raise ValueError("invalid shall schema: shalls must be a list")
    errors = [(i, validate_shall(item)) for i, item in enumerate(shalls)]
    errors = [(i, issues) for i, issues in errors if issues]
    if errors:
        raise ValueError(f"invalid shall schema: {errors}")
    return shalls


def generate_structured_shalls(
    source_requirement: str,
    annotated_evidence: list[dict],
    client,
    model: str,
    max_tokens: int = 8192,
) -> list[dict]:
    """Stage 3 RAG：根据证据值提取结果生成结构化 shall 列表。出错返回空列表。"""
    evidence_block = _build_evidence_block(annotated_evidence)
    if not annotated_evidence:
        _log.warning("generate_structured_shalls called with empty annotated_evidence — consider generate_norag_shalls")
    prompt = _STRUCTURED_GEN_PROMPT.format(
        source_requirement=source_requirement,
        evidence_block=evidence_block or "（无检索证据）",
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return _parse_shalls(resp.choices[0].message.content)
    except Exception as exc:
        _log.warning("generate_structured_shalls failed for %r: %s", source_requirement[:60], exc)
        return []


def generate_norag_shalls(
    source_requirement: str,
    client,
    model: str,
    max_tokens: int = 8192,
) -> list[dict]:
    """Stage 3 no-RAG：无证据的结构化基线生成。出错返回空列表。"""
    prompt = _NORAG_PROMPT.format(source_requirement=source_requirement)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return _parse_shalls(resp.choices[0].message.content)
    except Exception as exc:
        _log.warning("generate_norag_shalls failed for %r: %s", source_requirement[:60], exc)
        return []
