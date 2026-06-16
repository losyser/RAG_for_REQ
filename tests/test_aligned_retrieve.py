"""Tests for aligned_retrieve and generate_rag_v3 — all offline."""
from unittest.mock import MagicMock


def _resp(content):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


# ── aligned_retrieve ─────────────────────────────────────────────────────────

def _fake_searcher(filtered_results=None, unfiltered_results=None):
    s = MagicMock()
    filtered_results = filtered_results or []
    unfiltered_results = unfiltered_results or []
    s.filtered_vector_search.return_value = filtered_results
    s.filtered_bm25_search.return_value   = filtered_results
    s.vector_search.return_value = unfiltered_results
    s.bm25_search.return_value   = unfiltered_results
    return s


def _fake_analyzer_client(pairs_json: str):
    c = MagicMock()
    c.chat.completions.create.return_value = _resp(pairs_json)
    return c


def test_aligned_retrieve_uses_filtered_search():
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    ev = {"id": "E-PIPE-MAT-001", "text": "pipe material", "primary_component": "pipe", "primary_intent": "material"}
    searcher = _fake_searcher(filtered_results=[ev])
    client   = _fake_analyzer_client('[{"component":"pipe","intent":"material"}]')

    results, pairs = aligned_retrieve("管路耐腐蚀材料", searcher, client, "ds")

    assert pairs == [("pipe", "material")]
    assert any(r["id"] == "E-PIPE-MAT-001" for r in results)
    searcher.filtered_vector_search.assert_called()
    searcher.vector_search.assert_not_called()   # unfiltered not used


def test_aligned_retrieve_fallback_when_no_pairs():
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    ev = {"id": "E-FALLBACK-001", "text": "generic", "primary_component": "cooling_system", "primary_intent": "system_description"}
    searcher = _fake_searcher(unfiltered_results=[ev])
    client   = _fake_analyzer_client("[]")   # no valid pairs

    results, pairs = aligned_retrieve("任意需求", searcher, client, "ds")

    assert pairs == []
    assert any(r["id"] == "E-FALLBACK-001" for r in results)
    searcher.vector_search.assert_called()       # fallback used


def test_aligned_retrieve_deduplicates_across_pairs():
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    shared = {"id": "E-SHARED-001", "text": "shared", "primary_component": "pipe", "primary_intent": "material"}
    searcher = _fake_searcher(filtered_results=[shared])
    # two pairs but searcher returns same evidence for both
    client = _fake_analyzer_client(
        '[{"component":"pipe","intent":"material"},{"component":"pipe","intent":"corrosion_protection"}]'
    )
    results, pairs = aligned_retrieve("管路", searcher, client, "ds")
    ids = [r["id"] for r in results]
    assert ids.count("E-SHARED-001") == 1    # deduplicated


def test_aligned_retrieve_respects_max_total():
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    evs = [{"id": f"E-{i:03d}", "text": f"ev{i}", "primary_component": "pipe", "primary_intent": "material"}
           for i in range(20)]
    searcher = _fake_searcher(filtered_results=evs)
    client   = _fake_analyzer_client('[{"component":"pipe","intent":"material"}]')

    results, _ = aligned_retrieve("需求", searcher, client, "ds", max_total=5)
    assert len(results) <= 5


# ── parse_requirements_v3 ────────────────────────────────────────────────────

def test_parse_requirements_v3_resolves_refs():
    from cooling_rag_mg.req_generation_v2 import parse_requirements_v3
    ev_list = [
        {"id": "E-PIPE-MAT-001", "text": "t1"},
        {"id": "E-PIPE-CORR-002", "text": "t2"},
        {"id": "E-PIPE-WELD-003", "text": "t3"},
    ]
    raw = '{"engineering_requirements":[{"shall_statement":"管路应耐腐蚀。","verification_method":"检查","acceptance_criteria":["合格"],"evidence_refs":["E1","E3"]}]}'
    out = parse_requirements_v3(raw, ev_list)
    assert len(out) == 1
    assert out[0]["evidence_ids"] == ["E-PIPE-MAT-001", "E-PIPE-WELD-003"]


def test_parse_requirements_v3_empty_refs():
    from cooling_rag_mg.req_generation_v2 import parse_requirements_v3
    ev_list = [{"id": "E-001", "text": "t"}]
    raw = '{"engineering_requirements":[{"shall_statement":"待确认。","verification_method":"","acceptance_criteria":[],"evidence_refs":[]}]}'
    out = parse_requirements_v3(raw, ev_list)
    assert out[0]["evidence_ids"] == []


def test_parse_requirements_v3_ignores_unknown_refs():
    from cooling_rag_mg.req_generation_v2 import parse_requirements_v3
    ev_list = [{"id": "E-REAL-001", "text": "t"}]
    raw = '{"engineering_requirements":[{"shall_statement":"...","verification_method":"","acceptance_criteria":[],"evidence_refs":["E1","E99"]}]}'
    out = parse_requirements_v3(raw, ev_list)
    assert out[0]["evidence_ids"] == ["E-REAL-001"]   # E99 silently dropped


# ── generate_rag_v3 ──────────────────────────────────────────────────────────

def test_generate_rag_v3_end_to_end():
    from cooling_rag_mg.req_generation_v2 import generate_rag_v3
    ev_list = [
        {"id": "E-PIPE-MAT-001", "text": "pipe material spec", "primary_component": "pipe", "primary_intent": "material"},
        {"id": "E-PIPE-CORR-002", "text": "corrosion protection", "primary_component": "pipe", "primary_intent": "corrosion_protection"},
    ]
    client = MagicMock()
    client.chat.completions.create.return_value = _resp(
        '{"engineering_requirements":[{"shall_statement":"管路应采用铜镍合金。","verification_method":"材料证书","acceptance_criteria":["符合"],"evidence_refs":["E1"]}]}'
    )
    out = generate_rag_v3("管路材料", ev_list, client, model="ds")
    assert len(out) == 1
    assert out[0]["evidence_ids"] == ["E-PIPE-MAT-001"]
    assert "E-PIPE-CORR-002" not in out[0]["evidence_ids"]   # not cited by LLM


def test_generate_rag_v3_returns_empty_on_no_evidence():
    from cooling_rag_mg.req_generation_v2 import generate_rag_v3
    client = MagicMock()
    out = generate_rag_v3("需求", [], client, model="ds")
    assert out == []
    client.chat.completions.create.assert_not_called()
