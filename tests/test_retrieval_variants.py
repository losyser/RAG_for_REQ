# tests/test_retrieval_variants.py
from cooling_rag_mg.hybrid_fusion import rrf_fuse
from cooling_rag_mg.retrieval_variants import boundary_split_rate, retrieve_for_pairs


def test_rrf_default_unchanged():
    a = [{"id": "x"}, {"id": "y"}]; b = [{"id": "y"}, {"id": "z"}]
    assert [r["id"] for r in rrf_fuse([a, b])] == [r["id"] for r in rrf_fuse([a, b], weights=[1.0, 1.0])]


def test_rrf_weight_shifts_order():
    a = [{"id": "x"}]; b = [{"id": "y"}]
    assert rrf_fuse([a, b], weights=[0.2, 1.8])[0]["id"] == "y"


class _S:
    def filtered_vector_search(self, q, k, components, intents):
        return [{"id": f"v{j}"} for j in range(k)]
    def filtered_bm25_search(self, q, k, components, intents):
        return [{"id": f"b{j}"} for j in range(k)]


def test_modes_and_cap():
    s = _S()
    assert all(r["id"].startswith("v") for r in retrieve_for_pairs("q", [("c", "i")], s, mode="vector"))
    assert all(r["id"].startswith("b") for r in retrieve_for_pairs("q", [("c", "i")], s, mode="bm25"))
    assert len(retrieve_for_pairs("q", [("c", "i"), ("c2", "i2")], s, per_pair_k=12, max_total=20)) == 20


def test_boundary_split_rate_atomic_text_zero():
    r = boundary_split_rate(["当冷却水温度高于85°C时应报警。"], window=512, overlap=0.0)
    assert r["n_condition_value_sentences"] == 1 and r["split_pct"] == 0.0


def test_boundary_split_rate_small_window_splits():
    t = "x" * 120 + "当冷却水温度高于85°C时应报警。"
    r = boundary_split_rate([t], window=128, overlap=0.0)
    assert r["split_pct"] == 100.0
