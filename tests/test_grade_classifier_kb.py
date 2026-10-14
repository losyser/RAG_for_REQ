# tests/test_grade_classifier_kb.py
from cooling_rag_mg.grade_classifier import classify_grade, kb_has_clause, valid_citation_ids

KB = {
    "E-L1-CL": {"id": "E-L1-CL", "kb_tier": "L1", "text": "条款 7-25 1.6 冷却水温度高报警",
                "metadata": {"location": "P1935", "section_title": "条款 7-25 1.6"}},
    "E-L1-NOCL": {"id": "E-L1-NOCL", "kb_tier": "L1", "text": "cooling water shall be monitored",
                  "metadata": {"location": "", "section_title": "Cooling"}},
    "E-L2": {"id": "E-L2", "kb_tier": "L2", "text": "HT outlet 90 °C", "metadata": {}},
}


def test_unknown_id_is_uncited_and_numeric_is_x():
    cits = [{"kb_id": "E-NOT-IN-KB", "tier": "L1", "has_clause": "yes"}]
    assert valid_citation_ids(cits, KB) == []
    assert classify_grade("不超过 85°C", cits, kb_index=KB) == "X"


def test_model_claimed_tier_ignored_kb_tier_used():
    cits = [{"kb_id": "E-L2", "tier": "L1", "has_clause": "IACS"}]
    assert classify_grade("不超过 90°C", cits, kb_index=KB) == "B"


def test_l1_without_clause_locator_is_b():
    cits = [{"kb_id": "E-L1-NOCL", "tier": "L1", "has_clause": True}]
    assert kb_has_clause(KB["E-L1-NOCL"]) is False
    assert classify_grade("不超过 85°C", cits, kb_index=KB) == "B"


def test_l1_with_clause_locator_is_a():
    cits = [{"kb_id": "E-L1-CL"}]
    assert kb_has_clause(KB["E-L1-CL"]) is True
    assert classify_grade("不超过 85°C", cits, kb_index=KB) == "A"


def test_string_citation_with_valid_id_is_accepted():
    cits = ["E-L2 / 厂家指南 / L2"]
    assert valid_citation_ids(cits, KB) == ["E-L2"]
    assert classify_grade("90°C", cits, kb_index=KB) == "B"


def test_tbd_and_qualitative_still_c():
    assert classify_grade("{{TBD|unit:°C|ref:MAN}}", [], kb_index=KB) == "C"
    assert classify_grade("满足制造商要求", [], kb_index=KB) == "C"
