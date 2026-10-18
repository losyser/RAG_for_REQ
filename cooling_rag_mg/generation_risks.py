"""Independent offline risk annotations; lexical agreement never proves support."""
from __future__ import annotations

import copy
import re
import unicodedata
from decimal import Decimal

RISK_POLICY = "independent-reference-quantity-applicability-v1"
_QUANTITY = re.compile(
    r"(?P<op><=|>=|≤|≥|<|>|=)?\s*(?P<value>[+−-]?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>MPa|kPa|Pa|bar|°\s*C|℃|K|mm|cm|m³/h|m3/h|m/s|mg/L|g/L|ppm|dGH|%)(?![A-Za-z0-9])"
)


def quantities(text: str) -> list[tuple[str, str, str]]:
    text = unicodedata.normalize("NFKC", text).replace("−", "-")
    return [(str(Decimal(m["value"])), m["unit"].replace(" ", ""),
             {"≤": "<=", "≥": ">="}.get(m["op"], m["op"] or ""))
            for m in _QUANTITY.finditer(text)]


def assess_generation_risks(row: dict, evidence_scope: list[dict] | None) -> dict:
    """Only exact tuple presence in cited material is assessed, never entailment.

    Finite unit vocabulary, no conversion, inequalities/ranges are not solved.
    Missing/unparsed quantities and recorded applicability remain unverified.
    """
    citations = row.get("evidence_citations")
    ids = ([c.get("kb_id") for c in citations if isinstance(c, dict)]
           if isinstance(citations, list) else row.get("_reported_evidence_ids", row.get("evidence_ids", [])))
    if isinstance(ids, str):
        ids = [ids]
    ids = list(dict.fromkeys(i for i in ids if isinstance(i, str) and i))
    scope = {}
    ambiguous = set()
    for ev in evidence_scope or []:
        eid = ev.get("id")
        if eid in scope and scope[eid] != ev:
            ambiguous.add(eid)
        scope[eid] = ev
    missing = [i for i in ids if i not in scope] if evidence_scope is not None else []
    cited = [scope[i] for i in ids if i in scope and i not in ambiguous]
    issues = []
    if not ids:
        issues.append("no_citations")
    if missing:
        issues.append("citation_not_in_supplied_scope")
    if any(i in ambiguous for i in ids):
        issues.append("ambiguous_duplicate_citation")
    unknown_fields = {}
    for ev in cited:
        meta = ev.get("metadata") or {}
        absent = [k for k in ("engine_model", "applicable_condition")
                  if str(ev.get(k) or meta.get(k) or "").strip().lower()
                  in ("", "unknown", "null", "none", "tbd", "未知", "未记录")]
        if absent:
            unknown_fields[ev["id"]] = absent
    if unknown_fields or not cited:
        issues.append("model_or_condition_unknown")
    criteria = row.get("acceptance_criteria", [])
    if isinstance(criteria, str):
        criteria = [criteria]
    claims = quantities("\n".join(str(s) for s in [row.get("shall_statement", ""),
                        row.get("measurable_criterion", ""), *criteria]))
    available = set()
    for ev in cited:
        available.update(quantities(ev.get("text", "")))
        for value in ev.get("_extracted_values", []):
            available.update(quantities(" ".join(str(value.get(k, "")) for k in ("operator", "value_text", "unit"))))
    unmatched = [list(q) for q in claims if q not in available]
    if unmatched:
        issues.append("quantity_tuple_not_found_in_cited_material")
    return {"version": RISK_POLICY, "reference_scope": "unknown" if evidence_scope is None else "supplied_context",
            "citation_existence": "unknown" if evidence_scope is None or not ids else
                "missing_or_ambiguous" if missing or any(i in ambiguous for i in ids) else "present",
            "missing_ids": missing, "unknown_applicability_fields": unknown_fields,
            "numeric_consistency": "unknown_no_recognized_quantity" if not claims else
                "unmatched_requires_review" if unmatched else "lexical_tuple_match_only",
            "unmatched_quantities": unmatched, "semantic_support": "unknown", "applicability": "unknown",
            "issues": issues, "limitations": "finite units; no conversion, range reasoning, parameter-role or semantic verification"}


def annotate_generation_risks(rows: list[dict], evidence_scope: list[dict] | None,
                              *, policy: str = "legacy") -> list[dict]:
    if policy not in ("legacy", RISK_POLICY):
        raise ValueError("unknown generation risk policy")
    if policy == "legacy":
        return rows
    result = copy.deepcopy(rows)
    for row in result:
        row["_independent_risks"] = assess_generation_risks(row, evidence_scope)
        if row.get("support_status") == "verified_by_direct_evidence":
            row["_reported_support_status"] = row["support_status"]
            row["support_status"] = "need_confirmation"
    return result
