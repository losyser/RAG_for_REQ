import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ur", Path("scripts/110_unified_regrade.py"))
ur = importlib.util.module_from_spec(spec); spec.loader.exec_module(ur)

KB = {"E-1": {"id": "E-1", "kb_tier": "L2", "text": "outlet 80 °C", "metadata": {}},
      "L1-X-1": {"id": "L1-X-1", "kb_tier": "L1", "text": "3.3.1 test 0.4 MPa", "metadata": {"location": "3.3.1"}}}


def _er(mc, cits):
    return {"measurable_criterion": mc, "evidence_citations": cits, "shall_statement": "s"}


DATA = {"result_sets": [{"source_requirement_id": "OR1", "_evidence_values": {}, "engineering_requirements": [
    _er("80 °C", [{"kb_id": "E-1"}]),                       # B
    _er("0.4 MPa", [{"kb_id": "L1-X-1"}]),                  # A
    _er("{{TBD|°C|ref|c|i|h}}", [{"kb_id": "E-1"}]),        # C, TBD with citation
    _er("{{TBD|°C|ref|c|i|h}}", []),                        # C, TBD without citation
    _er("visually inspected", []),                          # C, no numeric pattern
    _er("0.3-0.6 bar", []),                                 # X only under range policy
]}]}


def test_range_policy_changes_grade_and_is_applied():
    legacy = ur.regrade(DATA, KB, "legacy")
    ranged = ur.regrade(DATA, KB, "numeric-ranges-v1")
    assert [e["_grade"] for e in ranged][-1] == "X"
    assert [e["_grade"] for e in legacy][-1] == "C"


def test_summary_counts_and_ci():
    s = ur.summarize(ur.regrade(DATA, KB, "numeric-ranges-v1"), KB, n_sets=1)
    assert (s["grade_A"], s["grade_B"], s["grade_C"], s["grade_X"]) == (1, 1, 3, 1)
    assert s["n_shalls"] == 6 and s["grade_AB_pct"] == 33.3
    assert s["citation_rate_pct"] == 50.0 and s["l1_citation_rate_pct"] == 16.7
    assert s["grade_X_ci"][0] > 0


def test_grade_c_breakdown_uses_valid_citations():
    gc = ur.grade_c_breakdown(ur.regrade(DATA, KB, "numeric-ranges-v1"), KB)
    br = gc["breakdown"]
    assert gc["total_grade_c"] == 3 and gc["total_shalls"] == 6
    assert br["TBD_with_evidence"]["count"] == 1
    assert br["TBD_no_evidence"]["count"] == 1
    assert br["qualitative"]["count"] == 1


def test_routing_counts_cover_every_row():
    rows = ur.regrade(DATA, KB, "numeric-ranges-v1")
    r = ur.routing(DATA, rows, KB)
    assert sum(r["routes"].values()) == 6 and sum(r["derivation"].values()) == 6
    assert r["routes"]["VERIFY_OR_REJECT"] == 1
