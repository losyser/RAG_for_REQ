from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.text_utils import simple_tokens


def _is_cuda_oom(exc: Exception) -> bool:
    message = str(exc).lower()
    return exc.__class__.__name__ == "OutOfMemoryError" or "cuda out of memory" in message


def _empty_cuda_cache() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def load_sentence_transformer(
    model_path: str,
    *,
    device: str = "cpu",
    label: str = "[Searcher]",
    model_kwargs: dict[str, Any] | None = None,
) -> SentenceTransformer:
    print(f"{label} Loading SentenceTransformer on device = {device}")
    kwargs = {"model_kwargs": model_kwargs} if model_kwargs else {}
    try:
        model = SentenceTransformer(model_path, device=device, **kwargs)
        print(f"{label} Model actual device = {model.device}")
        return model
    except Exception as exc:
        if device.startswith("cuda") and _is_cuda_oom(exc):
            print(f"{label} CUDA OOM while loading SentenceTransformer; falling back to CPU.")
            _empty_cuda_cache()
            model = SentenceTransformer(model_path, device="cpu")
            print(f"{label} Model actual device = {model.device}")
            return model
        raise



class NumpyFlatIP:
    """Exact inner-product index with the FAISS IndexFlatIP interface used here
    (``d``, ``ntotal``, ``search``, ``reconstruct``). Replaces faiss because faiss-cpu 1.13
    and torch 2.11 crash natively (access violation) in the same process on this Windows env."""

    def __init__(self, vectors: np.ndarray):
        self.vectors = np.ascontiguousarray(vectors, dtype="float32")
        self.d = int(self.vectors.shape[1])
        self.ntotal = int(self.vectors.shape[0])

    def search(self, q: np.ndarray, k: int):
        scores = np.asarray(q, dtype="float32") @ self.vectors.T
        kk = min(k, self.ntotal)
        order = np.argsort(-scores, axis=1, kind="stable")[:, :kk]
        top = np.take_along_axis(scores, order, axis=1)
        if kk < k:
            pad = k - kk
            order = np.hstack([order, -np.ones((order.shape[0], pad), dtype=order.dtype)])
            top = np.hstack([top, np.full((top.shape[0], pad), -np.inf, dtype="float32")])
        return top, order

    def reconstruct(self, idx: int, out: np.ndarray | None = None) -> np.ndarray:
        if out is None:
            return self.vectors[idx].copy()
        out[:] = self.vectors[idx]
        return out


class BuiltIndex:
    def __init__(self, records: list[dict[str, Any]], bm25: BM25Okapi, tokens: list[list[str]], faiss_index: Any, model_name: str):
        self.records = records
        self.bm25 = bm25
        self.tokens = tokens
        self.faiss_index = faiss_index
        self.model_name = model_name


def build_index(*, jsonl_path: str | Path, output_dir: str | Path, text_field: str, model_path: str, device: str = "cpu", normalize: bool = True) -> None:
    records = read_jsonl(jsonl_path)
    texts = [r.get(text_field, "") or r.get("search_text", "") or r.get("text", "") or r.get("chunk_text", "") for r in records]
    tokens = [simple_tokens(t) for t in texts]
    bm25 = BM25Okapi(tokens)

    model = load_sentence_transformer(model_path, device=device, label="[Build Index]")
    try:
        vectors = model.encode(texts, batch_size=32, normalize_embeddings=normalize, show_progress_bar=True)
    except Exception as exc:
        if str(model.device).startswith("cuda") and _is_cuda_oom(exc):
            print("[Build Index] CUDA OOM while encoding; retrying on CPU.")
            _empty_cuda_cache()
            model.to("cpu")
            vectors = model.encode(texts, batch_size=32, normalize_embeddings=normalize, show_progress_bar=True)
        else:
            raise
    vectors = np.asarray(vectors, dtype="float32")
    index = NumpyFlatIP(vectors)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "records.pkl").open("wb") as f:
        pickle.dump(records, f)
    with (out / "bm25.pkl").open("wb") as f:
        pickle.dump(bm25, f)
    with (out / "tokens.pkl").open("wb") as f:
        pickle.dump(tokens, f)
    np.save(out / "vectors.npy", index.vectors)
    (out / "model_path.txt").write_text(model_path, encoding="utf-8")


def load_index(index_dir: str | Path) -> BuiltIndex:
    p = Path(index_dir)
    with (p / "records.pkl").open("rb") as f:
        records = pickle.load(f)
    with (p / "bm25.pkl").open("rb") as f:
        bm25 = pickle.load(f)
    with (p / "tokens.pkl").open("rb") as f:
        tokens = pickle.load(f)
    if (p / "vectors.npy").exists():
        faiss_index = NumpyFlatIP(np.load(p / "vectors.npy"))
    else:  # legacy index directory written with faiss
        import faiss
        fi = faiss.read_index(str(p / "faiss.index"))
        faiss_index = NumpyFlatIP(np.vstack([fi.reconstruct(i) for i in range(fi.ntotal)]))
    model_name = (p / "model_path.txt").read_text(encoding="utf-8").strip()
    return BuiltIndex(records=records, bm25=bm25, tokens=tokens, faiss_index=faiss_index, model_name=model_name)


class HybridIndexSearcher:
    def __init__(self, built: BuiltIndex, *, device: str = "cpu", normalize: bool = True,
                 model: "SentenceTransformer | None" = None):
        self.built = built
        if model is not None:
            self.model = model
        else:
            self.model = load_sentence_transformer(built.model_name, device=device, label="[Searcher]")
        self.normalize = normalize

    def vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        try:
            qv = self.model.encode([query], normalize_embeddings=self.normalize)
        except Exception as exc:
            if str(self.model.device).startswith("cuda") and _is_cuda_oom(exc):
                print("[Searcher] CUDA OOM while encoding query; retrying on CPU.")
                _empty_cuda_cache()
                self.model.to("cpu")
                qv = self.model.encode([query], normalize_embeddings=self.normalize)
            else:
                raise
        qv = np.asarray(qv, dtype="float32")
        scores, idxs = self.built.faiss_index.search(qv, top_k)
        out = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            r = dict(self.built.records[idx])
            r["retrieval_score"] = float(score)
            r["retrieval_method"] = "vector"
            out.append(r)
        return out

    def bm25_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        q_tokens = simple_tokens(query)
        scores = self.built.bm25.get_scores(q_tokens)
        order = np.argsort(scores)[::-1][:top_k]
        out = []
        for idx in order:
            r = dict(self.built.records[int(idx)])
            r["retrieval_score"] = float(scores[int(idx)])
            r["retrieval_method"] = "bm25"
            out.append(r)
        return out

    # ── Metadata-filtered search ─────────────────────────────────────────────
    # Filters the index to records whose primary_component and primary_intent
    # match the requested values, then scores within that subset.
    # For the current KB size (~1200 records) this is fast enough in numpy.

    def _matching_indices(
        self,
        components: list[str] | None,
        intents: list[str] | None,
    ) -> list[int]:
        """Return record indices whose primary labels match the filter."""
        comp_set   = set(components) if components else None
        intent_set = set(intents)    if intents    else None
        return [
            i for i, r in enumerate(self.built.records)
            if (comp_set   is None or r.get("primary_component") in comp_set)
            and (intent_set is None or r.get("primary_intent")    in intent_set)
        ]

    def filtered_vector_search(
        self,
        query: str,
        top_k: int,
        *,
        components: list[str] | None = None,
        intents: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Vector search restricted to records matching (components, intents).

        Uses FAISS reconstruct to retrieve stored vectors for the filtered
        subset and computes cosine similarity in numpy — no index rebuild needed.
        Falls back to unfiltered vector_search if the subset is empty.
        """
        indices = self._matching_indices(components, intents)
        if not indices:
            return []

        # Encode query
        try:
            qv = self.model.encode([query], normalize_embeddings=self.normalize)
        except Exception as exc:
            if str(self.model.device).startswith("cuda") and _is_cuda_oom(exc):
                _empty_cuda_cache()
                self.model.to("cpu")
                qv = self.model.encode([query], normalize_embeddings=self.normalize)
            else:
                raise
        qv = np.asarray(qv, dtype="float32").flatten()

        # Reconstruct stored vectors for the subset
        d = self.built.faiss_index.d
        vecs = np.zeros((len(indices), d), dtype="float32")
        for j, idx in enumerate(indices):
            self.built.faiss_index.reconstruct(idx, vecs[j])

        scores = vecs @ qv          # cosine (vectors are normalised)
        order  = np.argsort(scores)[::-1][:top_k]
        return [
            {**self.built.records[indices[k]],
             "retrieval_score":  float(scores[k]),
             "retrieval_method": "vector_filtered"}
            for k in order
        ]

    def filtered_bm25_search(
        self,
        query: str,
        top_k: int,
        *,
        components: list[str] | None = None,
        intents: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """BM25 search restricted to records matching (components, intents)."""
        indices = self._matching_indices(components, intents)
        if not indices:
            return []

        q_tokens   = simple_tokens(query)
        all_scores = self.built.bm25.get_scores(q_tokens)

        ranked = sorted(indices, key=lambda i: all_scores[i], reverse=True)[:top_k]
        return [
            {**self.built.records[i],
             "retrieval_score":  float(all_scores[i]),
             "retrieval_method": "bm25_filtered"}
            for i in ranked
        ]
