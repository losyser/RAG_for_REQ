# cooling_rag_mg/grade_classifier.py
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Literal

CLASSIFIER_VERSION = "grade-v4-unit-token-boundaries"
RANGE_CLASSIFIER_VERSION = "grade-v5-numeric-range-boundaries"
# Grade measures criterion formatting and KB citation metadata, not semantic correctness.
# Only measurable_criterion is inspected, using the finite unit regex below.
Grade = Literal["A", "B", "C", "X"]

_TBD_PATTERN = re.compile(r"\{\{?\s*TBD\s*\|", re.IGNORECASE)
_NUM_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])[+-]?\d+(?:\.\d+)?\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|m3/h|dGH\b|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b)"
)
_RANGE_NUM_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])[+-]?\d+(?:\.\d+)?(?:\s*(?:-|–|—|~|至|到|to)\s*[+-]?\d+(?:\.\d+)?)?\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|m3/h|dGH\b|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b)"
)


_KBID = re.compile(r"\b(?:E|L1)-[A-Za-z0-9.\-]+")
_CLAUSE = re.compile(
    r"(\d+(?:\.\d+){1,}|\d+-\d+|Reg(?:ulation)?\.?\s*\d+|Rule\s*\d+|Table\s*\d|Tbl\.?\s*\d|"
    r"§\s*\d|条款|第\s*\d+\s*[条章节篇]|Pt\.?\s*\d+|Part\s*\d+|Ch(?:apter)?\.?\s*\d+|UR\s*[A-Z]\d+|CFR\s*\d+)"
)


def kb_has_clause(u: dict) -> bool:
    """KB 记录本身是否带有条款定位信息（位置、节标题或正文开头）。"""
    meta = u.get("metadata") or {}
    blob = " ".join([str(meta.get("location", "")), str(meta.get("section_title", "")),
                     (u.get("text") or "")[:200]])
    return bool(_CLAUSE.search(blob))


@lru_cache(maxsize=4)
def _citation_pattern(ids: tuple):
    return re.compile(r"(?<![\w.\-])(?:" + "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True)) + r")(?![\w.\-])")


def valid_citation_ids(evidence_citations, kb_index: dict) -> list[str]:
    """返回在 KB 中真实存在的被引 ID。兼容 dict 和字符串两种引用格式；去重并保持顺序。"""
    out: list[str] = []
    if isinstance(evidence_citations, (str, dict)):
        evidence_citations = [evidence_citations]
    elif not isinstance(evidence_citations, (list, tuple)):
        evidence_citations = []  # malformed model output (e.g. a number): no citation
    for c in evidence_citations:
        if isinstance(c, dict):
            cands = [str(c.get("kb_id") or "")]
        else:
            text = str(c)
            # Prefer full KB IDs, including Chinese clause suffixes; avoid partial-ID matches.
            cands = _citation_pattern(tuple(kb_index)).findall(text) if kb_index else []
        for cid in cands:
            cid = cid.strip()
            if cid and cid in kb_index and cid not in out:
                out.append(cid)
    return out


def _numeric_pattern(numeric_policy: str):
    if numeric_policy == "legacy":
        return _NUM_PATTERN
    if numeric_policy == "numeric-ranges-v1":
        return _RANGE_NUM_PATTERN
    raise ValueError(f"Unknown numeric policy: {numeric_policy}")


def classify_grade(measurable_criterion: str, evidence_citations: list, kb_index: dict | None = None, *, numeric_policy: str = "legacy") -> Grade:
    pattern = _numeric_pattern(numeric_policy)
    mc = unicodedata.normalize("NFKC", "" if measurable_criterion is None else str(measurable_criterion))
    if _TBD_PATTERN.search(mc):
        return "C"
    if not pattern.search(mc):
        return "C"
    if kb_index is not None:
        ids = valid_citation_ids(evidence_citations, kb_index)
        if not ids:
            return "X"
        if any(kb_index[i].get("kb_tier") == "L1" and kb_has_clause(kb_index[i]) for i in ids):
            return "A"
        return "B"
    # ---- 旧行为（kb_index=None），保留以兼容旧测试和旧结果 ----
    if not isinstance(evidence_citations, (list, tuple)):
        evidence_citations = [evidence_citations] if isinstance(evidence_citations, dict) else []
    if not evidence_citations:
        return "X"
    if any(isinstance(c, dict) and c.get("tier") == "L1" and c.get("has_clause", False)
           for c in evidence_citations):
        return "A"
    if any(isinstance(c, dict) and c.get("tier") in ("L1", "L2", "L3") for c in evidence_citations):
        return "B"
    return "X"


def classify_result_set(result_set: dict, kb_index: dict | None = None, *, numeric_policy: str = "legacy") -> dict:
    pattern = _numeric_pattern(numeric_policy)
    rs = dict(result_set)
    ers = []
    for er in rs.get("engineering_requirements", []):
        e = dict(er)
        e["_grade"] = classify_grade(er.get("measurable_criterion", ""),
                                     er.get("evidence_citations", []), kb_index, numeric_policy=numeric_policy)
        if kb_index is not None:
            e["_valid_citation_ids"] = valid_citation_ids(er.get("evidence_citations", []), kb_index)
        e["_grade_version"] = CLASSIFIER_VERSION if numeric_policy == "legacy" else RANGE_CLASSIFIER_VERSION
        e["_grade_numeric_policy"] = numeric_policy
        mc = unicodedata.normalize("NFKC", str(er.get("measurable_criterion") or ""))
        e["_grade_reason"] = ("placeholder" if _TBD_PATTERN.search(mc) else
            "no_recognized_numeric_unit" if not pattern.search(mc) else
            {"A": "numeric_and_l1_locator", "B": "numeric_and_citation", "X": "numeric_without_valid_citation"}[e["_grade"]])
        e["_grade_scope"] = "criterion_format_and_citation_metadata_not_correctness"
        ers.append(e)
    rs["engineering_requirements"] = ers
    return rs
