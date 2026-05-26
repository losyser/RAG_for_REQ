# -*- coding: utf-8 -*-
"""
Export engineering requirements to SysML-inspired XML.

The output is a lightweight custom XML serialisation whose field semantics are
aligned with the OMG SysML 1.6 Requirement block (OMG Document formal/2019-11-01)
but does NOT conform to the standard XMI interchange format.  It cannot be
directly imported by SysML tools (MagicDraw, Cameo, Papyrus) without a custom
importer.  The namespace URI and element names are project-specific.

Typical usage::

    from cooling_rag_mg.sysml_exporter import export_requirement_set

    xml_path = export_requirement_set(requirement_set_dict, output_path)
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

from cooling_rag_mg.text_utils import safe_text

# Project-specific namespace URI (SysML-inspired, not standard XMI)
_SYSML_NS = "http://www.omg.org/spec/SysML/20181001/CoolingRAG/Requirements"
_NS_PREFIX = "sysml"

ET.register_namespace(_NS_PREFIX, _SYSML_NS)


def _sysml(tag: str) -> str:
    return f"{{{_SYSML_NS}}}{tag}"


# ─────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────

def _sub(parent: ET.Element, tag: str, text: str | None = None, **attrs: str) -> ET.Element:
    el = ET.SubElement(parent, tag, **attrs)
    if text is not None:
        el.text = text
    return el


def _requirement_to_xml(
    req: dict[str, Any],
    parent: ET.Element,
    all_reqs: list[dict[str, Any]],
) -> ET.Element:
    """
    Serialise one engineering requirement (and its level-2 children) into XML.

    SysML Requirement block mandatory fields:
      id        → req["id"]
      name      → req["topic"]
      text      → req["shall_statement"]

    SysML relations:
      verifiedBy  → req["verification_method"]
      derivedFrom → req["parent_id"]  (when parent is a stakeholder requirement)

    Domain extensions (namespaced as sysml:*):
      sysml:Traceability      — evidence IDs with support classification
      sysml:QualityStatus     — support_status, applicability, risk
      sysml:AcceptanceCriteria
      sysml:QualityGateReport — injected by pipeline when quality_gate runs
      sysml:EngineeringRationale
    """
    req_el = ET.SubElement(parent, "Requirement")
    req_el.set("id", safe_text(req.get("id")))
    req_el.set("level", str(req.get("level", 1)))
    req_el.set("requirementType", safe_text(req.get("requirement_type", "other")))

    # ── SysML mandatory fields ──
    _sub(req_el, _sysml("Name"), safe_text(req.get("topic")))
    _sub(req_el, _sysml("Text"), safe_text(req.get("shall_statement")))

    # ── SysML relations ──
    method = safe_text(req.get("verification_method"))
    if method:
        ver_el = _sub(req_el, _sysml("VerifiedBy"))
        ver_el.set("method", method)

    parent_id = safe_text(req.get("parent_id"))
    if parent_id:
        _sub(req_el, _sysml("DerivedFrom"), refId=parent_id)

    # ── Evidence traceability ──
    evidence_ids: list[str] = req.get("evidence_ids") or []
    if evidence_ids:
        trace_el = _sub(req_el, _sysml("Traceability"))
        status = safe_text(req.get("support_status"))
        for eid in evidence_ids:
            ev_el = _sub(trace_el, "Evidence", id=safe_text(eid))
            ev_el.set("supportStatus", status)

    # ── Quality status ──
    qs_el = _sub(req_el, _sysml("QualityStatus"))
    _sub(qs_el, "SupportStatus", safe_text(req.get("support_status")))
    risk = safe_text(req.get("risk_if_unmet"))
    if risk:
        _sub(qs_el, "RiskIfUnmet", risk)
    for constraint in (req.get("applicability_constraints") or []):
        _sub(qs_el, "ApplicabilityConstraint", safe_text(constraint))

    # ── Acceptance criteria ──
    criteria: list[str] = req.get("acceptance_criteria") or []
    if criteria:
        ac_el = _sub(req_el, _sysml("AcceptanceCriteria"))
        for c in criteria:
            _sub(ac_el, "Criterion", safe_text(c))

    # ── Engineering rationale ──
    rationale = safe_text(req.get("engineering_rationale"))
    if rationale:
        _sub(req_el, _sysml("EngineeringRationale"), rationale)

    # ── Quality gate report (injected by pipeline) ──
    qg: dict[str, Any] | None = req.get("quality_gate_report")
    if qg:
        qg_el = _sub(req_el, _sysml("QualityGateReport"))
        qg_el.set("passed", str(qg.get("overall_passed", False)).lower())
        qg_el.set("score", str(qg.get("score", 0.0)))
        for chk in (qg.get("checks") or []):
            chk_el = _sub(qg_el, "Check")
            chk_el.set("dimension", safe_text(chk.get("dimension")))
            chk_el.set("passed", str(chk.get("passed", False)).lower())
            chk_el.set("severity", safe_text(chk.get("severity")))
            if chk.get("message"):
                _sub(chk_el, "Message", safe_text(chk.get("message")))
            if chk.get("suggestion"):
                _sub(chk_el, "Suggestion", safe_text(chk.get("suggestion")))

    # ── Recursively nest direct children (next level) ──
    rid = safe_text(req.get("id"))
    current_level = req.get("level", 1)
    children = [
        r for r in all_reqs
        if safe_text(r.get("parent_id")) == rid and r.get("level", 1) == current_level + 1
    ]
    for child in children:
        _requirement_to_xml(child, req_el, all_reqs)

    return req_el


# ─────────────────────────────────────────────
# 公共接口
# ─────────────────────────────────────────────

def export_requirement_set(
    requirement_set: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """
    Export one requirement set (output of engineering_requirement_agent) to
    SysML-aligned XML.

    Args:
        requirement_set: Dict matching the agent's output schema
                         (requirement_set_id, source_requirement_id, stakeholder,
                          engineering_requirements, relationships, evidence_gaps, …).
        output_path:     Destination .xml file path (parent dirs created automatically).

    Returns:
        Resolved Path of the written file.
    """
    root = ET.Element("RequirementSet")
    root.set("setId",                safe_text(requirement_set.get("requirement_set_id")))
    root.set("sourceRequirementId",  safe_text(requirement_set.get("source_requirement_id")))
    root.set("stakeholder",          safe_text(requirement_set.get("stakeholder")))
    root.set("generationBasis",      safe_text(requirement_set.get("generation_basis", "")))
    root.set("generatedAt",          datetime.now().isoformat(timespec="seconds"))

    # Professional summary
    summary = safe_text(requirement_set.get("professional_summary"))
    if summary:
        _sub(root, "ProfessionalSummary", summary)

    # Assumptions
    assumptions: list[str] = requirement_set.get("assumptions") or []
    if assumptions:
        asmp_el = _sub(root, "Assumptions")
        for a in assumptions:
            _sub(asmp_el, "Assumption", safe_text(a))

    # Engineering requirements (level-1 at top; children nested recursively)
    all_reqs: list[dict[str, Any]] = requirement_set.get("engineering_requirements") or []
    top_level = [r for r in all_reqs if r.get("level", 1) == 1]
    reqs_el = _sub(root, "EngineeringRequirements",
                   count=str(len(all_reqs)))
    for req in top_level:
        _requirement_to_xml(req, reqs_el, all_reqs)

    # Relationships
    relationships: list[dict[str, Any]] = requirement_set.get("relationships") or []
    if relationships:
        rels_el = _sub(root, _sysml("Relationships"))
        for rel in relationships:
            rel_el = _sub(rels_el, "Relationship",
                          source=safe_text(rel.get("source")),
                          target=safe_text(rel.get("target")),
                          type=safe_text(rel.get("type")))
            desc = safe_text(rel.get("description"))
            if desc:
                rel_el.text = desc

    # Evidence gaps
    gaps: list[dict[str, Any]] = requirement_set.get("evidence_gaps") or []
    if gaps:
        gaps_el = _sub(root, "EvidenceGaps", count=str(len(gaps)))
        for gap in gaps:
            gap_el = _sub(gaps_el, "Gap",
                          relatedRequirementId=safe_text(gap.get("related_requirement_id")),
                          gapType=safe_text(gap.get("gap_type")))
            _sub(gap_el, "Description", safe_text(gap.get("description")))
            suggested = safe_text(gap.get("suggested_document_update"))
            if suggested:
                _sub(gap_el, "SuggestedDocumentUpdate", suggested)

    # Confirmation items
    items: list[dict[str, Any]] = requirement_set.get("confirmation_items") or []
    if items:
        conf_el = _sub(root, "ConfirmationItems")
        for item in items:
            ci_el = _sub(conf_el, "Item")
            _sub(ci_el, "Statement", safe_text(item.get("item")))
            reason = safe_text(item.get("reason"))
            if reason:
                _sub(ci_el, "Reason", reason)

    # Write file
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(out), encoding="utf-8", xml_declaration=True)
    return out.resolve()


def export_batch(
    requirement_sets: list[dict[str, Any]],
    output_dir: str | Path,
) -> list[Path]:
    """Export multiple requirement sets; each saved as <setId>.xml."""
    out_dir = Path(output_dir)
    paths = []
    for rs in requirement_sets:
        sid = safe_text(rs.get("requirement_set_id")) or "RS-unknown"
        paths.append(export_requirement_set(rs, out_dir / f"{sid}.xml"))
    return paths
