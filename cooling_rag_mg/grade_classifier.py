# cooling_rag_mg/grade_classifier.py
from __future__ import annotations

import re
from typing import Literal

Grade = Literal["A", "B", "C", "X"]

_TBD_PATTERN = re.compile(r"\{\{TBD\|")
_NUM_PATTERN = re.compile(
    r"\d+\.?\d*\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b)"
)


def classify_grade(measurable_criterion: str, evidence_citations: list[dict]) -> Grade:
    """将 shall 的 measurable_criterion 分类为 Grade A/B/C/X。

    A：精确值 + L1 引用 + has_clause=True
    B：有数值 + 任意引用（非 Grade A）
    C：{{TBD}} 占位符 或 无数值（定性表述）
    X：有数值 + 无任何引用
    """
    # 鲁棒处理：部分 LLM 可能把 measurable_criterion 返回为数字/None 而非字符串。
    mc = "" if measurable_criterion is None else str(measurable_criterion)

    if _TBD_PATTERN.search(mc):
        return "C"

    if not _NUM_PATTERN.search(mc):
        return "C"

    if not evidence_citations:
        return "X"

    # 仅采信结构化（dict）引用：含 tier/has_clause 才计为有效引用。
    # isinstance 守卫避免某些 LLM 把引用返回为字符串时崩溃；非 dict 引用
    # 不在此处采信——跨模型时由带 KB 校验的独立重分级处理（见论文跨模型小节）。
    has_l1_clause = any(
        isinstance(c, dict) and c.get("tier") == "L1" and c.get("has_clause", False)
        for c in evidence_citations
    )
    if has_l1_clause:
        return "A"

    has_citation = any(
        isinstance(c, dict) and c.get("tier") in ("L1", "L2", "L3")
        for c in evidence_citations
    )
    if has_citation:
        return "B"
    return "X"


def classify_result_set(result_set: dict) -> dict:
    """对单个 source requirement 的所有 shall 添加 _grade 字段，返回副本。"""
    rs = dict(result_set)
    classified_ers = []
    for er in rs.get("engineering_requirements", []):
        er_copy = dict(er)
        er_copy["_grade"] = classify_grade(
            er.get("measurable_criterion", ""),
            er.get("evidence_citations", []),
        )
        classified_ers.append(er_copy)
    rs["engineering_requirements"] = classified_ers
    return rs
