import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context, compact_evidence, normalize_agent_output
from cooling_rag_mg.ui_evidence_contracts import diagnose_numeric_selection

ROOT = Path(__file__).resolve().parents[1]


def evidence(eid="E1", text="Temperature <= 80°C\nCondition: startup."):
    return {"id": eid, "text": text, "llm_judge": {"support_type": "direct"}, "metadata": {"applicable_condition": ["startup"], "engine_model": "M1"}, "_extracted_values": [{"value_text": "80", "operator": "<=", "unit": "°C"}]}


def context(ev=None):
    return {"requirement_id": "R1", "sub_requirements": [{"selected_results": [ev or evidence()]}]}


def row(**extra):
    return {"id": "ER1", "shall_statement": "System shall meet the specified limit", "acceptance_criteria": ["80°C"], "evidence_ids": ["E1"], "support_status": "verified_by_direct_evidence", "verification_method": "test", **extra}


def test_deferred_budget_preserves_text_instead_of_ellipsis():
    raw = evidence()
    assert compact_evidence(raw, text_limit=0)["text"] == raw["text"]
    result = compact_requirement_context(context(raw))
    ev = result["supported_evidence"][0]
    assert "Condition: startup" in ev["text"]
    assert ev["_extracted_values"][0]["unit"] == "°C"
    assert ev["_extracted_values"][0]["operator"] == "<="


def test_paragraph_and_metadata_omissions_are_explicit():
    ev = evidence(text="x" * 2000)
    ev["metadata"]["applicable_condition"] = ["long" * 300]
    result = compact_requirement_context(context(ev))["supported_evidence"][0]
    assert result["text"] == "" and result["_context_status"] == "partial_unknown"
    assert "applicable_condition" in result["_omitted_metadata_fields"]
    assert result["_applicability"] == "unknown"


def test_ui_schema_preserves_hierarchy_and_legacy_strings():
    data = {"engineering_requirements": [row(level=2, parent_id="ROOT", acceptance_criteria="acceptable", evidence_ids="E1")], "requirement_set_id": "ROOT"}
    out = normalize_agent_output(data, "R1")
    req = out["engineering_requirements"][0]
    assert req["level"] == 2 and req["parent_id"] == "ROOT"
    assert req["acceptance_criteria"] == ["acceptable"] and req["evidence_ids"] == ["E1"]
    assert "measurable_criterion" not in req
    assert out["_validation_report"]["semantic_support"] == "unknown"
    assert data["engineering_requirements"][0]["evidence_ids"] == "E1"


def test_invalid_and_misaligned_references_are_traced_not_verified():
    data = {"source_requirement_id": "WRONG", "engineering_requirements": [row(evidence_ids=["E-UNKNOWN", "E-UNKNOWN"])], "relationships": [{"source": "MISSING", "target": "ER1"}]}
    out = normalize_agent_output(data, "R1", evidence_scope=[compact_evidence(evidence())])
    req = out["engineering_requirements"][0]
    assert req["evidence_ids"] == [] and req["_reported_evidence_ids"] == ["E-UNKNOWN"]
    assert req["support_status"] == "evidence_gap"
    assert out["source_requirement_id"] == "R1" and out["relationships"] == []
    codes = {i["code"] for i in out["_validation_report"]["issues"]}
    assert {"source_id_mismatch", "reference_not_in_supplied_support_context", "dangling_relationship_removed"} <= codes


def test_missing_conditions_and_semantically_wrong_reference_remain_unknown():
    ev = evidence(text="Unrelated pressure 10 bar")
    ev["metadata"] = {}
    out = normalize_agent_output({"engineering_requirements": [row()]}, "R1", evidence_scope=[compact_evidence(ev)])
    assert out["engineering_requirements"][0]["evidence_ids"] == ["E1"]
    assert out["_validation_report"]["semantic_support"] == "unknown"
    assert any(i["code"] == "cited_applicability_unknown" for i in out["_validation_report"]["issues"])


def test_duplicate_requirements_rejected_without_guessing_relationships():
    with pytest.raises(ValueError, match="duplicate UI"):
        normalize_agent_output({"engineering_requirements": [row(), row()]}, "R1")


def test_reference_order_dedup_and_background_beyond_display_cap():
    subs = [{"selected_results": [evidence("E2"), evidence("E1"), evidence("E2")]}]
    for i in range(9):
        ev = evidence(f"BG{i}"); ev["llm_judge"]["support_type"] = "background"
        subs.append({"selected_results": [ev]})
    ctx = compact_requirement_context({"sub_requirements": subs}, max_evidence=1)
    assert [e["id"] for e in ctx["supported_evidence"]] == ["E2"]
    assert ctx["_omitted_supported_evidence_ids"] == ["E1"]
    assert "BG8" in ctx["_background_evidence_ids"]


def test_nonempty_mapping_keeps_hard_filter_but_reports_zero_results(monkeypatch):
    import cooling_rag_mg.requirement_analyzer as analyzer
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    monkeypatch.setattr(analyzer, "analyze_requirement", lambda *a: [("wrong", "wrong")])
    search = MagicMock()
    search.filtered_vector_search.return_value = []; search.filtered_bm25_search.return_value = []
    search.vector_search.return_value = [evidence("potential-rescue")]
    diagnostic = {}
    got, pairs = aligned_retrieve("requirement", search, None, "offline", diagnostics=diagnostic)
    assert got == [] and pairs == [("wrong", "wrong")]
    search.vector_search.assert_not_called()
    assert diagnostic["nonempty_mapping_zero_results"] is True
    assert diagnostic["mapping_correctness"] == "unknown"


def test_numeric_first_omits_nonnumeric_without_claiming_recall():
    units = [evidence(f"N{i}") for i in range(13)] + [{"id": "IMPORTANT-QUALITATIVE", "_extracted_values": []}]
    out = diagnose_numeric_selection(units)
    assert len(out["selected_ids"]) == 12
    assert out["omitted_non_numeric_ids"] == ["IMPORTANT-QUALITATIVE"]
    assert out["relevance"] == "unknown"


@pytest.mark.parametrize("invalid_schema", [False, True])
def test_actual_langgraph_nodes_with_mocked_model(monkeypatch, invalid_schema):
    import cooling_rag_mg.engineering_requirement_agent as agent
    captured = []
    def fake_completion(*args, **kwargs):
        captured.append(json.loads(kwargs["messages"][1]["content"]))
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"engineering_requirements": "invalid" if invalid_schema else [row(evidence_ids=["E1", "WRONG"])]})))])
    monkeypatch.setattr(agent, "cached_completion", fake_completion)
    monkeypatch.setattr(agent, "repair_json_with_deepseek", lambda *a: pytest.fail("repair API must not run"))
    monkeypatch.setattr(agent, "get_config", lambda: SimpleNamespace(deepseek=SimpleNamespace(enabled=True, make_client=lambda: object(), model="offline", temperature=0, max_tokens_requirement_agent=1000)))
    result = agent.build_graph().invoke({"requirement": {"requirement_id": "R1"}, "retrieval_context": context(), "errors": []})
    assert "startup" in captured[0]["retrieval_context"]["supported_evidence"][0]["text"]
    if invalid_schema:
        assert result["output"]["generation_mode"] == "fallback"
        assert result["output"]["_validation_report"]["semantic_support"] == "unknown"
        return
    req = result["output"]["engineering_requirements"][0]
    assert req["evidence_ids"] == ["E1"] and req["support_status"] == "need_confirmation"
    assert req["_semantic_support"] == "unknown"


def test_saved_ui_contexts_retain_real_text_without_mutation():
    path = ROOT / "data/search_results/batch_20260730_164747/all_requirements_results.json"
    records = json.loads(path.read_text(encoding="utf-8"))["requirements"]
    old = copy.deepcopy(records)
    outputs = [compact_requirement_context(r) for r in records]
    assert any(e["text"] not in ("", "...") for r in outputs for e in r["supported_evidence"])
    assert records == old


def test_legacy_background_guard_cannot_leave_direct_claim_without_refs():
    result = normalize_agent_output({"engineering_requirements": [row()], "_background_evidence_ids": ["E1"]}, "R1")
    req = result["engineering_requirements"][0]
    assert req["evidence_ids"] == [] and req["support_status"] == "evidence_gap"
    assert any(i["code"] == "background_reference_removed" for i in result["_validation_report"]["issues"])


def test_saved_ui_compaction_hashes_are_process_stable():
    import subprocess, sys, os
    code = r"""
+import json,hashlib
+from pathlib import Path
+from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context
+rows=[]
+for p in sorted(Path('data/search_results').glob('batch_*/all_requirements_results.json')):
+    rows.extend(compact_requirement_context(r) for r in json.loads(p.read_text(encoding='utf-8')).get('requirements',[]))
+print(hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest())
+""".replace("\n+", "\n")
    hashes = [subprocess.check_output([sys.executable, "-B", "-c", code], cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"}, text=True).strip() for seed in ("1", "17", "123")]
    assert len(set(hashes)) == 1 and len(hashes[0]) == 64


def test_unfiltered_fallback_respects_explicit_max_total(monkeypatch):
    import cooling_rag_mg.requirement_analyzer as analyzer
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    monkeypatch.setattr(analyzer, "analyze_requirement", lambda *a: [])
    search = MagicMock()
    search.vector_search.return_value = [{"id": f"E{i}"} for i in range(10)]
    search.bm25_search.return_value = []
    diagnostic = {}
    rows, pairs = aligned_retrieve("r", search, None, "offline", max_total=3, diagnostics=diagnostic)
    assert len(rows) == 3 and pairs == []
    assert diagnostic["unfiltered_fallback_used"] and diagnostic["result_count"] == 3
    with pytest.raises(ValueError, match="positive"):
        aligned_retrieve("r", search, None, "offline", max_total=0)
