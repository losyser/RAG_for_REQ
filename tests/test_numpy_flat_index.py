# faiss-cpu 1.13 + torch 2.11 crash natively on this Windows env once faiss has run;
# index_store therefore uses an exact NumPy inner-product index with FAISS IndexFlatIP semantics.
import pickle

import numpy as np

from cooling_rag_mg.index_store import NumpyFlatIP, load_index


def _vecs():
    rng = np.random.default_rng(0)
    v = rng.normal(size=(50, 8)).astype("float32")
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_search_matches_bruteforce_topk():
    v = _vecs(); q = v[3:4]
    idx = NumpyFlatIP(v)
    scores, ids = idx.search(q, 5)
    expect = np.argsort(-(v @ q[0]))[:5]
    assert scores.shape == (1, 5) and ids.shape == (1, 5)
    assert list(ids[0]) == list(expect) and ids[0][0] == 3


def test_search_k_larger_than_n_pads_minus_one():
    v = _vecs()[:3]
    _, ids = NumpyFlatIP(v).search(v[:1], 5)
    assert list(ids[0][3:]) == [-1, -1]


def test_reconstruct_and_d():
    v = _vecs(); idx = NumpyFlatIP(v)
    out = np.zeros(8, dtype="float32"); idx.reconstruct(7, out)
    assert idx.d == 8 and np.allclose(out, v[7])


def test_load_index_reads_vectors_npy():
    # pytest tmp_path hits PermissionError on this Windows env (see test_grounding); use a repo-local dir
    from pathlib import Path
    tmp_path = Path("data/debug/test_numpy_flat_index"); tmp_path.mkdir(parents=True, exist_ok=True)
    v = _vecs()
    for name, obj in [("records.pkl", [{"id": str(i)} for i in range(50)]), ("bm25.pkl", None), ("tokens.pkl", [])]:
        with open(tmp_path / name, "wb") as f:
            pickle.dump(obj, f)
    np.save(tmp_path / "vectors.npy", v)
    (tmp_path / "model_path.txt").write_text("m", encoding="utf-8")
    built = load_index(tmp_path)
    assert isinstance(built.faiss_index, NumpyFlatIP) and built.faiss_index.d == 8
