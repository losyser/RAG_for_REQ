# cooling_rag_mg/kb_provenance.py
"""KB 出处审计：把每条证据单元归入出处组，并给出建议动作。

组别：
  DRAFT   —— KB_DRAFT_v1，由 LLM 起草（scripts/56），不是从原文切分的
  CCS2025 —— 从 CCS 入级规范 PDF 按页提取的 L1 单元（scripts/63b）
  ORIG    —— 原始语料，source_document 编号 S01–S59，从原文切分
  LATE    —— 后期补充（编号 ≥S60 或没有编号），需要逐条对照原文核实
"""
from __future__ import annotations

import re

REGULATORY_TYPES = {"ship_rule", "standard"}
_SNUM = re.compile(r"^S(\d+)\b")
_LATE_MIN = 60
# 注意：只匹配 "Consolidated from"；"SOLAS Consolidated Edition" 是官方版本名，不算综合单元
_SYNTH_MARKERS = ("Consolidated from", "consolidated from", "Industry consensus", "General Practice",
                  "Multiple sources", "Best Practice", "综合")
# 已核实的标题误标（见计划 §0）：键为 source_document 中的子串
KNOWN_MISATTRIBUTED = {
    "ISO 8861": "ISO 8861:1998 = Engine-room ventilation in diesel-engined ships",
    "Unified Requirements M3.1 Cooling": "IACS UR M3 = Speed governor and overspeed protective device",
    "Unified Requirements E10 Machinery Control": "IACS UR E10 = Test specification for type approval",
}


def source_document(u: dict) -> str:
    return ((u.get("metadata") or {}).get("source_document") or "").strip()


def provenance_group(u: dict) -> str:
    src = source_document(u)
    if src == "KB_DRAFT_v1" or str(u.get("id", "")).startswith("E-DRAFT-"):
        return "DRAFT"
    if str(u.get("id", "")).startswith("L1-CCS2025"):
        return "CCS2025"
    m = _SNUM.match(src)
    if m and int(m.group(1)) < _LATE_MIN:
        return "ORIG"
    return "LATE"


def audit_flags(u: dict) -> list[str]:
    flags: list[str] = []
    src = source_document(u)
    meta = u.get("metadata") or {}
    head = (u.get("text") or "")[:300]
    if provenance_group(u) == "DRAFT":
        flags.append("llm_drafted")
    if any(k in src for k in KNOWN_MISATTRIBUTED):
        flags.append("misattributed_title")
    blob = " ".join([head, src, str(meta.get("topic", "")), str(meta.get("location", ""))])
    if any(mk in blob for mk in _SYNTH_MARKERS):
        flags.append("synthesized")
    if u.get("kb_tier") == "L1" and meta.get("source_type") not in REGULATORY_TYPES:
        flags.append("l1_nonregulatory")
    return flags


def proposed_action(u: dict) -> str:
    flags = audit_flags(u)
    if {"llm_drafted", "misattributed_title", "synthesized"} & set(flags):
        return "DROP"
    grp = provenance_group(u)
    if grp == "LATE":
        return "VERIFY"
    if "l1_nonregulatory" in flags:
        return "RETIER_L2"
    return "KEEP"
