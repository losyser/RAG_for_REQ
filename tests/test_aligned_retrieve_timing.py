import cooling_rag_mg.requirement_analyzer as ra
from cooling_rag_mg.coverage_retrieval import aligned_retrieve


class _S:
    def filtered_vector_search(self, q, k, components, intents):
        return [{"id": f"v{j}"} for j in range(k)]
    def filtered_bm25_search(self, q, k, components, intents):
        return [{"id": f"b{j}"} for j in range(k)]
    def vector_search(self, q, k):
        return [{"id": "fv"}]
    def bm25_search(self, q, k):
        return [{"id": "fb"}]


def test_timing_filled_for_pairs(monkeypatch):
    monkeypatch.setattr(ra, "analyze_requirement", lambda t, c, m: [("pump", "redundancy")])
    t: dict = {}
    ev, pairs = aligned_retrieve("q", _S(), None, "m", per_pair_k=2, max_total=20, timing=t)
    assert pairs == [("pump", "redundancy")] and len(ev) == 4
    assert set(t) == {"stage1_s", "retrieval_s"}


def test_timing_filled_on_fallback(monkeypatch):
    monkeypatch.setattr(ra, "analyze_requirement", lambda t, c, m: [])
    t: dict = {}
    aligned_retrieve("q", _S(), None, "m", timing=t)
    assert set(t) == {"stage1_s", "retrieval_s"}


def test_timing_optional(monkeypatch):
    monkeypatch.setattr(ra, "analyze_requirement", lambda t, c, m: [("pump", "redundancy")])
    ev, _ = aligned_retrieve("q", _S(), None, "m", per_pair_k=2)
    assert len(ev) == 4
