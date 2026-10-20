# cooling_rag_mg/review_routing.py
"""派生类型（ISO/IEC/IEEE 29148 风格的来源关系）、引用证据之间的冲突检测、复核路由。均为确定性规则。"""
from __future__ import annotations

import re
import unicodedata

from cooling_rag_mg.grade_classifier import valid_citation_ids
from cooling_rag_mg.numeric_norm import extract_numbers


_UNIT = re.compile(r"\d\s*(°C|MPa|kPa|bar|%|m³/h|L/min|rpm|kW|mm|min|分钟|秒|s(?![A-Za-z]))")
_UNIT_NORM = {"分钟": "min", "秒": "s"}


def _unit_of(s: str) -> str:
    """返回紧跟在数字后面的第一个物理单位（NFKC 后 ℃ 变为 °C）；没有则返回空串。"""
    m = _UNIT.search(unicodedata.normalize("NFKC", s or ""))
    return _UNIT_NORM.get(m.group(1), m.group(1)) if m else ""


def derivation_type(er: dict, kb: dict) -> str:
    mc = str(er.get("measurable_criterion") or "")
    ids = valid_citation_ids(er.get("evidence_citations", []), kb)
    if not ids:
        return "Unsupported"
    if re.search(r"\{\{?TBD\|", mc):
        return "Deferred"
    nums = extract_numbers(mc)
    if not nums:
        return "Synthesized" if len(ids) >= 2 else "Derived"
    per_unit = {i: set(extract_numbers(kb[i].get("text", ""))) for i in ids}
    if any(set(nums) <= s for s in per_unit.values()):
        return "Direct"
    if set(nums) <= set().union(*per_unit.values()) and len(ids) >= 2:
        return "Synthesized"
    return "Derived"


def conflict_flag(er: dict, kb: dict, evidence_values: dict) -> dict | None:
    ids = valid_citation_ids(er.get("evidence_citations", []), kb)
    unit = _unit_of(str(er.get("measurable_criterion") or ""))
    if len(ids) < 2 or not unit:
        return None
    sets = {}
    for i in ids:
        vals = {n for v in evidence_values.get(i, []) if _unit_of(str(v.get("value_text", "")) + " " + str(v.get("unit", ""))) == unit
                for n in extract_numbers(v.get("value_text", ""))}
        if vals:
            sets[i] = vals
    if len(sets) < 2:
        return None
    keys = list(sets)
    pairs = [[a, b] for x, a in enumerate(keys) for b in keys[x + 1:] if not (sets[a] & sets[b])]
    return {"unit": unit, "units": keys, "values": {k: sorted(v) for k, v in sets.items()},
            "candidate_pairs": pairs, "status": "candidate_requires_applicability_review",
            "authority_decision": None,
            "reason": "disjoint numeric tokens sharing a unit; parameter, conditions, applicability and source version unverified"} if pairs else None



def review_route(er: dict, kb: dict, evidence_values: dict) -> tuple[str, str]:
    if conflict_flag(er, kb, evidence_values):
        return "ADJUDICATE", "rule candidate: disjoint values share a unit; human parameter/applicability/version adjudication required"
    d = derivation_type(er, kb)
    g = er.get("_grade")
    if d == "Unsupported" and g == "X":
        return "VERIFY_OR_REJECT", "numeric value without a valid KB citation"
    if d == "Deferred":
        return "OPEN_ITEM", "value deferred to named source document"
    if g == "A" and d == "Direct":
        return "SPOT_CHECK", "numeric tokens occur in an L1 clause-referenced unit; semantic applicability unverified"
    ids = valid_citation_ids(er.get("evidence_citations", []), kb)
    if ids and all(kb[i].get("kb_tier") != "L1" for i in ids):
        return "ENGINEER_CONFIRM", "cites manufacturer/operational guidance only (tier-b)"
    return "ENGINEER_CONFIRM", f"derivation type {d}"


def derivation_assessment(er: dict, kb: dict) -> dict:
    """Versioned honest interpretation of the legacy token-overlap heuristic."""
    legacy = derivation_type(er, kb)
    nums = extract_numbers(str(er.get("measurable_criterion") or ""))
    classification = {"Direct":"numeric_tokens_in_one_cited_unit",
        "Synthesized":"numeric_tokens_across_cited_units" if nums else "multiple_citations_no_numeric",
        "Derived":"unmatched_numeric" if nums else "single_citation_no_numeric",
        "Unsupported":"no_valid_citation", "Deferred":"placeholder_deferred"}[legacy]
    return {"version":"routing-v2", "legacy_type":legacy, "classification":classification,
            "valid_citation_ids":valid_citation_ids(er.get("evidence_citations", []), kb),
            "criterion_numeric_tokens":nums, "mathematical_derivation_verified":False,
            "semantic_support_verified":False, "requires_review":True,
            "derivation_chain_status":"not_verified" if er.get("derivation_chain") else "not_provided"}
