# tests/test_sensitivity_index_check.py
"""scripts/99 decides whether the alternative (mpnet) index must be rebuilt by
checking for the index artefacts on disk.  build_index() now writes vectors.npy
(NumpyFlatIP) instead of faiss.index, so the readiness check must follow the
current artefact, otherwise the index is rebuilt on every run."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("sv", Path("scripts/99_retrieval_sensitivity.py"))
sv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sv)


def test_index_ready_follows_vectors_npy(tmp_path):
    d = tmp_path / "idx"
    d.mkdir()
    assert sv.index_ready(d) is False
    (d / "vectors.npy").write_bytes(b"x")
    (d / "records.pkl").write_bytes(b"x")
    (d / "bm25.pkl").write_bytes(b"x")
    (d / "tokens.pkl").write_bytes(b"x")
    assert sv.index_ready(d) is True


def test_index_ready_rejects_legacy_only_dir(tmp_path):
    d = tmp_path / "legacy"
    d.mkdir()
    (d / "faiss.index").write_bytes(b"x")
    assert sv.index_ready(d) is False
