"""Offline, bounded evidence contracts. No inference of missing historical context."""
from __future__ import annotations

import json
import re

CONTRACT_VERSION = "evidence-v1-complete-records"
SELECTION_POLICY = "numeric-first-stable-first-reference-v1"
MIXED_SELECTION_POLICY = "numeric-first-reserve-one-nonnumeric-v1"
OPTIONAL_VALUE_FIELDS = ("parameter", "conditions", "model", "source_span")


def validate_values(values: object) -> list[dict]:
    if not isinstance(values, list):
        raise ValueError("values must be a list")
    out = []
    for i, value in enumerate(values):
        if not isinstance(value, dict):
            raise ValueError(f"values[{i}] must be an object")
        for key in ("value_text", "operator", "unit"):
            if not isinstance(value.get(key), str):
                raise ValueError(f"values[{i}].{key} must be a string")
        if not value["value_text"].strip():
            raise ValueError(f"values[{i}].value_text is empty")
        if value["operator"] not in ("", "<", ">", "<=", ">=", "=", "≤", "≥", "≈", "最大", "up to", "max", "大于", "min."):
            raise ValueError(f"values[{i}].operator is invalid")
        for key in OPTIONAL_VALUE_FIELDS:
            if key in value and value[key] is not None and not isinstance(value[key], str):
                raise ValueError(f"values[{i}].{key} must be string or null")
        out.append(dict(value))
    return out


def ordered_evidence_ids(requirements: list[dict]) -> list[str]:
    """First occurrence in saved v3 references, NOT recovered retrieval rank."""
    seen = {}
    for er in requirements:
        ids = er.get("evidence_ids", [])
        if not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids):
            raise ValueError("evidence_ids must be a list of nonempty strings")
        for eid in ids:
            seen.setdefault(eid, None)
    return list(seen)


def select_evidence(evidence: list[dict], limit: int = 12, *, policy: str = SELECTION_POLICY) -> list[dict]:
    if policy not in (SELECTION_POLICY, MIXED_SELECTION_POLICY):
        raise ValueError("unknown evidence selection policy")
    if limit < 1:
        raise ValueError("evidence limit must be positive")
    unique = {}
    for eu in evidence:
        eid = eu.get("id")
        if not isinstance(eid, str) or not eid:
            raise ValueError("evidence id must be a nonempty string")
        validate_values(eu.get("_extracted_values", []))
        if eid in unique and eu != unique[eid]:
            raise ValueError(f"conflicting duplicate evidence: {eid}")
        unique.setdefault(eid, eu)
    # Python sort is stable; the input sequence must itself be ordered.
    ordered = sorted(unique.values(), key=lambda eu: not bool(eu.get("_extracted_values")))
    selected = ordered[:limit]
    # Explicit coverage hypothesis, not a relevance/authority score. At limit=1
    # retain legacy numeric priority; reserving both classes is impossible.
    if policy == MIXED_SELECTION_POLICY and limit > 1 and selected and all(e.get("_extracted_values") for e in selected):
        nonnumeric = next((e for e in ordered if not e.get("_extracted_values")), None)
        if nonnumeric is not None:
            selected[-1] = nonnumeric
    return selected


def bounded_context(text: str, limit: int) -> tuple[str, int]:
    """Retain whole blank-line-delimited paragraphs, including adjacent table rows.

    An oversized paragraph is omitted, never sliced into a context-free value.
    This conservative boundary cannot establish semantic completeness across paragraphs.
    """
    if not isinstance(text, str) or limit < 1:
        raise ValueError("context requires text and a positive limit")
    blocks = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    picked, used = [], 0
    for block in blocks:
        cost = len(block) + (2 if picked else 0)
        if used + cost <= limit:
            picked.append(block)
            used += cost
    return "\n\n".join(picked), len(blocks) - len(picked)


def bounded_value_records(values: list[dict], limit: int = 1600) -> tuple[str, int]:
    """Keep each complete record or explicitly omit it; null means not recorded."""
    lines, used = [], 0
    for value in validate_values(values):
        record = dict(value)
        for key in OPTIONAL_VALUE_FIELDS:
            record.setdefault(key, None)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        cost = len(line) + bool(lines)
        if used + cost <= limit:
            lines.append(line)
            used += cost
    return "\n".join(lines), len(values) - len(lines)


def applicability_record(eu: dict, limit: int = 700) -> str:
    meta = eu.get("metadata") or {}
    record = {key: eu.get(key) or meta.get(key) or None for key in (
        "manufacturer", "engine_model", "applicable_condition", "location",
        "applicability_level", "limitation", "unsupported_requirements",
    )}
    # Preserve the entire applicability record, or flag its absence. Never trim a condition.
    text = json.dumps(record, ensure_ascii=False, sort_keys=True)
    if len(text) > limit:
        return '{"status":"omitted_over_budget","applicability":"unknown"}'
    return text


def validate_shall(item: object) -> list[str]:
    errors = []
    if not isinstance(item, dict):
        return ["shall must be an object"]
    for key in ("shall_statement", "measurable_criterion", "applicable_condition", "verification_method"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            errors.append(f"{key} must be a nonempty string (use explicit unknown where appropriate)")
    criteria = item.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria or any(not isinstance(c, str) or not c.strip() for c in criteria):
        errors.append("acceptance_criteria must be a nonempty list of nonempty strings")
    citations = item.get("evidence_citations")
    if not isinstance(citations, list):
        errors.append("evidence_citations must be a list")
    else:
        for i, citation in enumerate(citations):
            if not isinstance(citation, dict):
                errors.append(f"citation[{i}] must be an object")
                continue
            for key in ("kb_id", "source"):
                if not isinstance(citation.get(key), str) or not citation[key].strip():
                    errors.append(f"citation[{i}].{key} must be a nonempty string")
            if citation.get("tier") not in ("L1", "L2", "L3"):
                errors.append(f"citation[{i}].tier is invalid")
            if not isinstance(citation.get("has_clause"), bool):
                errors.append(f"citation[{i}].has_clause must be boolean")
    return errors
