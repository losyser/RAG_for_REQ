# tests/test_grade_classifier.py
from cooling_rag_mg.grade_classifier import classify_grade, classify_result_set


def test_grade_c_for_tbd_placeholder():
    mc = "{{TBD|unit:°C|ref:MAN|component:pump|intent:temp|hint:温度}}"
    assert classify_grade(mc, [{"tier": "L1", "has_clause": True}]) == "C"


def test_grade_c_for_no_numeric_value():
    mc = "应满足制造商规定的温度限值"
    assert classify_grade(mc, [{"tier": "L1", "has_clause": True}]) == "C"


def test_grade_a_for_l1_clause_precise_value():
    mc = "不超过 85°C"
    citations = [{"tier": "L1", "has_clause": True}]
    assert classify_grade(mc, citations) == "A"


def test_grade_b_for_l1_no_clause():
    mc = "不超过 85°C"
    citations = [{"tier": "L1", "has_clause": False}]
    assert classify_grade(mc, citations) == "B"


def test_grade_b_for_l2_citation():
    mc = "压差小于 0.05 bar"
    citations = [{"tier": "L2", "has_clause": False}]
    assert classify_grade(mc, citations) == "B"


def test_grade_b_for_l3_range_value():
    mc = "流量不低于 120 L/min"
    citations = [{"tier": "L3", "has_clause": False}]
    assert classify_grade(mc, citations) == "B"


def test_grade_x_for_value_with_no_citation():
    mc = "响应时间不超过 10 s"
    assert classify_grade(mc, []) == "X"


def test_classify_result_set_adds_grade_to_each_shall():
    result_set = {
        "source_requirement_id": "OR001",
        "engineering_requirements": [
            {
                "measurable_criterion": "{{TBD|unit:°C|ref:X|component:p|intent:t|hint:h}}",
                "evidence_citations": [],
            },
            {
                "measurable_criterion": "不超过 85°C",
                "evidence_citations": [{"tier": "L1", "has_clause": True}],
            },
            {
                "measurable_criterion": "10 秒内完成",
                "evidence_citations": [],
            },
        ],
    }
    classified = classify_result_set(result_set)
    grades = [er["_grade"] for er in classified["engineering_requirements"]]
    assert grades == ["C", "A", "X"]


def test_grade_x_for_unknown_tier_citation():
    mc = "不超过 85°C"
    citations = [{"tier": "L4", "has_clause": False}]
    assert classify_grade(mc, citations) == "X"


def test_grade_c_for_none_criterion():
    assert classify_grade(None, []) == "C"
