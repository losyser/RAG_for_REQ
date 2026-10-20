import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("fe", Path("scripts/107_fill_truncated_sets.py"))
fe = importlib.util.module_from_spec(spec); spec.loader.exec_module(fe)

KB = {"E1": {"id": "E1", "kb_tier": "L2", "text": "HT outlet 90 °C", "metadata": {}}}


def test_only_empty_sets_regenerated_with_saved_evidence():
    sets = [
        {"source_requirement_id": "OR1", "engineering_requirements": [{"measurable_criterion": "x"}],
         "_evidence_values": {"E1": []}},
        {"source_requirement_id": "OR2", "engineering_requirements": [],
         "_evidence_values": {"E1": [{"value_text": "90 °C", "unit": "°C"}]}},
    ]
    calls = []
    def gen(req_id, annotated):
        calls.append((req_id, [a["id"] for a in annotated], annotated[0]["_extracted_values"]))
        return [{"measurable_criterion": "90°C", "evidence_citations": [{"kb_id": "E1"}]}]
    out, filled = fe.fill_empty_sets(sets, KB, gen)
    assert filled == ["OR2"]
    assert calls == [("OR2", ["E1"], [{"value_text": "90 °C", "unit": "°C"}])]
    assert out[0] is sets[0]
    assert out[1]["engineering_requirements"][0]["_grade"] == "B"
    assert out[1]["_refilled_max_tokens"] == 8192


def test_set_without_evidence_left_untouched():
    sets = [{"source_requirement_id": "OR3", "engineering_requirements": [], "_evidence_values": {}}]
    out, filled = fe.fill_empty_sets(sets, KB, lambda r, a: [{"measurable_criterion": "1°C"}])
    assert filled == [] and out[0]["engineering_requirements"] == []
