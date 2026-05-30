def test_coverage_retrieve_unions_and_dedups():
    from cooling_rag_mg.coverage_retrieval import coverage_retrieve

    class FakeSearcher:
        def vector_search(self, q, k):
            return {"a": [{"id": "E1", "text": "t1"}], "b": [{"id": "E2", "text": "t2"}]}.get(q, [])

        def bm25_search(self, q, k):
            return {"a": [{"id": "E2", "text": "t2"}], "b": [{"id": "E3", "text": "t3"}]}.get(q, [])

    out = coverage_retrieve(["a", "b"], FakeSearcher(), per_query_k=10, max_total=10)
    ids = sorted(d["id"] for d in out)
    assert ids == ["E1", "E2", "E3"]


def test_coverage_retrieve_empty_queries():
    from cooling_rag_mg.coverage_retrieval import coverage_retrieve

    class S:
        def vector_search(self, q, k):
            return []

        def bm25_search(self, q, k):
            return []

    assert coverage_retrieve([], S(), per_query_k=10, max_total=10) == []
