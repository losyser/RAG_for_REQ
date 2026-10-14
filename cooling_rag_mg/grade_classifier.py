# cooling_rag_mg/grade_classifier.py
from __future__ import annotations

import re
from typing import Literal

Grade = Literal["A", "B", "C", "X"]

_TBD_PATTERN = re.compile(r"\{\{TBD\|")
_NUM_PATTERN = re.compile(
    r"\d+\.?\d*\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b)"
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


def valid_citation_ids(evidence_citations, kb_index: dict) -> list[str]:
    """返回在 KB 中真实存在的被引 ID。兼容 dict 和字符串两种引用格式；去重并保持顺序。"""
    out: list[str] = []
    for c in evidence_citations or []:
        if isinstance(c, dict):
            cands = [str(c.get("kb_id") or "")]
        else:
            cands = _KBID.findall(str(c))
        for cid in cands:
            cid = cid.strip()
            if cid and cid in kb_index and cid not in out:
                out.append(cid)
    return out


def classify_grade(measurable_criterion: str, evidence_citations: list, kb_index: dict | None = None) -> Grade:
    mc = "" if measurable_criterion is None else str(measurable_criterion)
    if _TBD_PATTERN.search(mc):
        return "C"
    if not _NUM_PATTERN.search(mc):
        return "C"
    if kb_index is not None:
        ids = valid_citation_ids(evidence_citations, kb_index)
        if not ids:
            return "X"
        if any(kb_index[i].get("kb_tier") == "L1" and kb_has_clause(kb_index[i]) for i in ids):
            return "A"
        return "B"
    # ---- 旧行为（kb_index=None），保留以兼容旧测试和旧结果 ----
    if not evidence_citations:
        return "X"
    if any(isinstance(c, dict) and c.get("tier") == "L1" and c.get("has_clause", False)
           for c in evidence_citations):
        return "A"
    if any(isinstance(c, dict) and c.get("tier") in ("L1", "L2", "L3") for c in evidence_citations):
        return "B"
    return "X"


def classify_result_set(result_set: dict, kb_index: dict | None = None) -> dict:
    rs = dict(result_set)
    ers = []
    for er in rs.get("engineering_requirements", []):
        e = dict(er)
        e["_grade"] = classify_grade(er.get("measurable_criterion", ""),
                                     er.get("evidence_citations", []), kb_index)
        if kb_index is not None:
            e["_valid_citation_ids"] = valid_citation_ids(er.get("evidence_citations", []), kb_index)
        ers.append(e)
    rs["engineering_requirements"] = ers
    return rs
