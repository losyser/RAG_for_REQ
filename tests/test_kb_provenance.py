# tests/test_kb_provenance.py
from cooling_rag_mg.kb_provenance import provenance_group, audit_flags, proposed_action


def _u(id_, src, tier="L1", stype="ship_rule", text="x", topic=""):
    return {"id": id_, "text": text, "kb_tier": tier,
            "metadata": {"source_document": src, "source_type": stype, "topic": topic}}


def test_draft_group_and_drop():
    u = _u("E-DRAFT-ALARM-001", "KB_DRAFT_v1", stype="project_guide")
    assert provenance_group(u) == "DRAFT"
    assert proposed_action(u) == "DROP"
    assert "llm_drafted" in audit_flags(u)


def test_ccs2025_group_keep():
    u = _u("L1-CCS2025-7-251.6-001", "CCS《钢质海船入级规范》2025")
    assert provenance_group(u) == "CCS2025"
    assert proposed_action(u) == "KEEP"


def test_orig_numbering_below_60():
    assert provenance_group(_u("E-PUMP-001", "S42 MAN 49/60DF Project Guide")) == "ORIG"


def test_late_numbering_and_unnumbered():
    assert provenance_group(_u("E-X-1", "S66 IACS Unified Requirements M72 Hydraulic Testing")) == "LATE"
    assert provenance_group(_u("E-X-2", "Wärtsilä 46F Series Product Manual", tier="L2")) == "LATE"
    assert proposed_action(_u("E-X-1", "S66 IACS Unified Requirements M72 Hydraulic Testing")) == "VERIFY"


def test_known_misattribution_drop():
    u = _u("E-ISO8861-001", "S63 ISO 8861:1998 Shipbuilding Cooling Systems Requirements", stype="standard")
    assert "misattributed_title" in audit_flags(u)
    assert proposed_action(u) == "DROP"
    u2 = _u("E-IACS-M3-001", "S60 IACS Unified Requirements M3.1 Cooling Systems")
    assert proposed_action(u2) == "DROP"


def test_synthesized_marker_drop():
    u = _u("E-PARAM-HT-001", "S60 IACS Unified Requirements M3.1 Cooling Systems",
           text="Standard Parameter Limits\n(Consolidated from IACS UR M3.1, ISO 8861)")
    assert "synthesized" in audit_flags(u)
    assert proposed_action(u) == "DROP"


def test_solas_consolidated_edition_not_flagged():
    u = _u("E-SOLAS-COOL-001", "S49 SOLAS 2024 Chapter II-1 Regulation 26",
           text="SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26")
    assert "synthesized" not in audit_flags(u)
    assert proposed_action(u) == "KEEP"


def test_orig_nonregulatory_l1_retier():
    u = _u("E-HT-009", "S21 Caterpillar Cooling Systems Application and Installation Guide",
           stype="installation_guide")
    assert proposed_action(u) == "RETIER_L2"


def test_orig_regulatory_l1_keep():
    u = _u("E-SW-ALARM-001", "S43 ABS Marine Vessel Rules Part 4 2021", stype="ship_rule")
    assert proposed_action(u) == "KEEP"
