"""UI-specific structural checks; never semantic verification or a v4 schema adapter."""
from __future__ import annotations
import copy
import json
import re
import hashlib
from collections import Counter

from .evidence_contracts import bounded_value_records, select_evidence


def bounded_ui_excerpt(raw: str, limit: int) -> dict:
    """Keep the existing fitting paragraphs; only rescue an otherwise empty body.

    Spans are Unicode character offsets, end-exclusive, in the exact original text.
    A rescued fragment is never described as condition-complete.
    """
    if not isinstance(raw, str) or limit < 1:
        raise ValueError("excerpt requires text and a positive character budget")
    blocks = []
    cursor = 0
    for match in list(re.finditer(r"\n\s*\n", raw)) + [None]:
        end = match.start() if match else len(raw)
        piece = raw[cursor:end]
        start = cursor + len(piece) - len(piece.lstrip())
        stop = end - (len(piece) - len(piece.rstrip()))
        if start < stop:
            blocks.append((start, stop))
        if match:
            cursor = match.end()
    chosen, used = [], 0
    for start, end in blocks:
        cost = end - start + (2 if chosen else 0)
        if used + cost <= limit:
            chosen.append((start, end))
            used += cost
    rescued = bool(blocks) and not chosen
    boundary = "whole_paragraphs"
    if rescued:
        start, end = blocks[0]
        stop = min(end, start + limit)
        candidates = [start + m.end() for m in re.finditer(r"[。！？!?；;\n]|\.(?=\s|$)", raw[start:stop])]
        preferred = [p for p in candidates if p - start >= max(1, limit // 2)]
        if preferred:
            stop = preferred[-1]
            boundary = "sentence_or_line_boundary_not_semantic_completeness"
        else:
            boundary = "hard_character_boundary"
        chosen = [(start, stop)]
    text = "\n\n".join(raw[start:end] for start, end in chosen)
    partial = rescued or len(chosen) < len(blocks)
    return {"text": text, "_context_status": "empty_source_unknown" if not blocks else "partial_unknown" if partial else "all_paragraphs_retained_not_semantic_verification",
            "_text_truncated": partial, "_fragment_fallback": rescued, "_fragment_boundary": boundary,
            "_source_text_spans": [list(span) for span in chosen], "_source_span_unit": "unicode_character_end_exclusive",
            "_source_text_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "_source_text_chars": len(raw), "_retained_text_chars": len(text), "_text_budget_chars": limit,
            "_omitted_context_paragraphs": len(blocks) - (0 if rescued else len(chosen))}


def retain_ui_evidence(out: dict, evidence: dict, text_limit: int) -> dict:
    raw = evidence.get("text") or ""
    if not isinstance(raw, str):
        raise ValueError("evidence text must be a string")
    if text_limit == 0:  # deferred budget, not a zero-character truncation
        out["text"] = raw
        out["_context_status"] = "pending_budget"
    else:
        out.update(bounded_ui_excerpt(raw, text_limit))
    meta = evidence.get("metadata") or {}
    omitted_fields = []
    for key in ("unsupported_requirements", "normalized_summary", "limitation", "applicable_condition", "engine_model", "manufacturer"):
        value = meta.get(key, out.get(key))
        if len(json.dumps(value, ensure_ascii=False)) > 700:
            value = None
            omitted_fields.append(key)
        out[key] = value
    out["_omitted_metadata_fields"] = omitted_fields
    out["_missing_applicability_fields"] = [k for k in ("applicable_condition", "engine_model") if not out.get(k)]
    # Already extracted values only: no new extraction and no fabricated parameters.
    values = evidence.get("_extracted_values", [])
    records, omitted = bounded_value_records(values)
    out["_extracted_values"] = [json.loads(line) for line in records.splitlines()]
    out["_omitted_parameter_records"] = omitted
    out["_extraction_status"] = evidence.get("_extraction_status", "unknown_historical")
    out["_semantic_support"] = "unknown"
    out["_applicability"] = "unknown"
    return out


def prepare_ui_output(obj: dict, requirement_id: str, evidence_scope: list[dict] | None = None) -> dict:
    """Preserve the UI hierarchy schema and record lossy normalization explicitly."""
    if not isinstance(obj, dict):
        raise ValueError("UI output must be an object")
    obj = copy.deepcopy(obj)
    issues = []
    def issue(path, code, reported=None):
        issues.append({"path": path, "code": code, "reported": reported})
    for key in ("engineering_requirements", "relationships", "assumptions", "evidence_gaps", "confirmation_items"):
        if key in obj and not isinstance(obj[key], list):
            raise ValueError(f"UI {key} must be a list")
    if obj.get("source_requirement_id") not in (None, "", requirement_id):
        issue("source_requirement_id", "source_id_mismatch", obj["source_requirement_id"])
        obj["source_requirement_id"] = requirement_id
    scope = {e["id"]: e for e in evidence_scope or [] if isinstance(e.get("id"), str)}
    cleaned = []
    for index, row in enumerate(obj.get("engineering_requirements", [])):
        path = f"engineering_requirements[{index}]"
        if not isinstance(row, dict) or not isinstance(row.get("shall_statement"), str) or not row["shall_statement"].strip():
            issue(path, "invalid_shall_rejected", row)
            continue
        for key in ("acceptance_criteria", "evidence_ids", "applicability_constraints"):
            value = row.get(key, [])
            if isinstance(value, str):
                issue(path + "." + key, "legacy_string_wrapped_without_splitting", value)
                value = [value] if value.strip() else []
            if not isinstance(value, list):
                issue(path + "." + key, "invalid_list_replaced", value)
                value = []
            if any(not isinstance(v, str) or not v.strip() for v in value):
                issue(path + "." + key, "invalid_list_items_removed", value)
            row[key] = [v for v in value if isinstance(v, str) and v.strip()]
        ids = list(dict.fromkeys(row["evidence_ids"]))
        row["_reported_evidence_ids"] = list(ids)
        blocked = set(obj.get("_background_evidence_ids", []) or [])
        removed_background = [eid for eid in ids if eid in blocked]
        if removed_background:
            issue(path + ".evidence_ids", "background_reference_removed", removed_background)
            ids = [eid for eid in ids if eid not in blocked]
            row["support_status"] = "need_confirmation" if ids else "evidence_gap"
        if evidence_scope is not None:
            invalid = [eid for eid in ids if eid not in scope]
            if invalid:
                issue(path + ".evidence_ids", "reference_not_in_supplied_support_context", invalid)
                ids = [eid for eid in ids if eid in scope]
                row["support_status"] = "need_confirmation" if ids else "evidence_gap"
            for eid in ids:
                ev = scope[eid]
                if ev.get("_context_status") == "partial_unknown" or ev.get("_omitted_metadata_fields") or ev.get("_omitted_parameter_records") or ev.get("_constraint_status") == "omitted_over_budget":
                    issue(path, "cited_context_incomplete", eid)
                    if row.get("support_status") == "verified_by_direct_evidence":
                        row["support_status"] = "need_confirmation"
                if not ev.get("text", "").strip() or ev.get("text", "").strip() == "...":
                    issue(path, "cited_body_empty_or_placeholder", eid)
                    if row.get("support_status") == "verified_by_direct_evidence":
                        row["support_status"] = "need_confirmation"
                if ev.get("_missing_applicability_fields"):
                    issue(path, "cited_applicability_unknown", eid)
        row["evidence_ids"] = ids
        if not ids and row.get("support_status") == "verified_by_direct_evidence":
            issue(path, "direct_claim_without_citation", row["support_status"])
            row["support_status"] = "evidence_gap"
        row["_semantic_support"] = "unknown"
        row["_applicability"] = "unknown"
        cleaned.append(row)
    ids = [r.get("id") for r in cleaned if r.get("id")]
    duplicates = [rid for rid, n in Counter(ids).items() if n > 1]
    if duplicates:
        raise ValueError(f"duplicate UI requirement IDs: {duplicates}")
    obj["engineering_requirements"] = cleaned
    relationships = obj.get("relationships", [])
    if any(not isinstance(rel, dict) for rel in relationships):
        issue("relationships", "non_object_relationships_removed")
        obj["relationships"] = [rel for rel in relationships if isinstance(rel, dict)]
    obj["_validation_report"] = {"version": "ui-structure-reference-v1", "semantic_support": "unknown", "applicability": "unknown", "reference_scope": "supplied_support_context" if evidence_scope is not None else "unknown", "issues": issues}
    return obj


def finish_ui_audit(obj: dict, before: dict) -> dict:
    report = obj["_validation_report"]
    issues = report["issues"]
    previous = {r.get("id"): r for r in before.get("engineering_requirements", []) if r.get("id")}
    ids = {r["id"] for r in obj.get("engineering_requirements", [])}
    root = obj.get("requirement_set_id")
    reference_ids = ids | {root, obj.get("source_requirement_id")}
    for row in obj.get("engineering_requirements", []):
        old = previous.get(row["id"])
        if old:
            for field in ("acceptance_criteria", "evidence_ids", "support_status", "verification_method"):
                if old.get(field) != row.get(field):
                    issues.append({"path": row["id"] + "." + field, "code": "normalizer_changed_field", "reported": old.get(field)})
        if row.get("parent_id") not in reference_ids:
            issues.append({"path": row["id"] + ".parent_id", "code": "dangling_parent", "reported": row.get("parent_id")})
    valid = []
    for rel in obj.get("relationships", []):
        if rel.get("source") not in reference_ids or rel.get("target") not in reference_ids:
            issues.append({"path": "relationships", "code": "dangling_relationship_removed", "reported": rel})
        else:
            valid.append(rel)
    obj["relationships"] = valid
    return obj


def diagnose_numeric_selection(evidence: list[dict], limit: int = 12) -> dict:
    """Describe the existing policy; do not change ranking or run retrieval."""
    selected = select_evidence(evidence, limit)
    ids = [e["id"] for e in selected]
    omitted = [e for e in evidence if e["id"] not in ids]
    return {"policy": "numeric-first-stable-first-reference-v1", "selected_ids": ids,
            "omitted_ids": list(dict.fromkeys(e["id"] for e in omitted)),
            "omitted_non_numeric_ids": list(dict.fromkeys(e["id"] for e in omitted if not e.get("_extracted_values"))),
            "relevance": "unknown", "authority_coverage": "unknown", "semantic_support": "unknown"}
