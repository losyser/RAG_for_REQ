# tests/test_review_routing.py
from cooling_rag_mg.review_routing import conflict_flag, derivation_type, review_route

KB = {
    "E1": {"id": "E1", "kb_tier": "L1", "text": "条款 3.2.1 高温报警 90 °C", "metadata": {"location": "3.2.1"}},
    "E2": {"id": "E2", "kb_tier": "L2", "text": "HT outlet alarm 95 °C", "metadata": {}},
    "E3": {"id": "E3", "kb_tier": "L2", "text": "pressure 3 bar", "metadata": {}},
}


def er(mc, cits, grade):
    return {"measurable_criterion": mc, "evidence_citations": [{"kb_id": c} for c in cits], "_grade": grade}


def test_direct_with_unit_variants():
    assert derivation_type(er("≤ 90℃", ["E1"], "A"), KB) == "Direct"


def test_synthesized_across_units():
    assert derivation_type(er("90°C；3 bar", ["E1", "E3"], "A"), KB) == "Synthesized"


def test_derived_when_number_not_in_text():
    assert derivation_type(er("88°C", ["E1"], "A"), KB) == "Derived"


def test_unsupported_and_deferred():
    assert derivation_type(er("90°C", [], "X"), KB) == "Unsupported"
    assert derivation_type(er("{{TBD|unit:°C}}", ["E1"], "C"), KB) == "Deferred"


def test_conflict_disjoint_values_same_unit():
    ev = {"E1": [{"value_text": "90 °C", "unit": "°C"}], "E2": [{"value_text": "95 °C", "unit": "°C"}]}
    f = conflict_flag(er("90°C", ["E1", "E2"], "A"), KB, ev)
    assert f is not None and set(f["units"]) == {"E1", "E2"}
    assert review_route(er("90°C", ["E1", "E2"], "A"), KB, ev)[0] == "ADJUDICATE"


def test_unit_not_confused_by_letter_s():
    from cooling_rag_mg.review_routing import _unit_of
    assert _unit_of("pressure loss across strainers 3 bar") == "bar"
    assert _unit_of("响应时间 ≤ 2 秒") == "s"
    assert _unit_of("满足要求 as specified") == ""


def test_routes():
    assert review_route(er("90°C", ["E1"], "A"), KB, {})[0] == "SPOT_CHECK"
    assert review_route(er("95°C", ["E2"], "B"), KB, {})[0] == "ENGINEER_CONFIRM"
    assert review_route(er("{{TBD|unit:°C}}", ["E1"], "C"), KB, {})[0] == "OPEN_ITEM"
    assert review_route(er("90°C", [], "X"), KB, {})[0] == "VERIFY_OR_REJECT"
