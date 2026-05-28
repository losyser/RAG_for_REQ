from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import faiss
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
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "records.pkl").open("wb") as f:
        pickle.dump(records, f)
    with (out / "bm25.pkl").open("wb") as f:
        pickle.dump(bm25, f)
    with (out / "tokens.pkl").open("wb") as f:
        pickle.dump(tokens, f)
    faiss.write_index(index, str(out / "faiss.index"))
    (out / "model_path.txt").write_text(model_path, encoding="utf-8")


def load_index(index_dir: str | Path) -> BuiltIndex:
    p = Path(index_dir)
    with (p / "records.pkl").open("rb") as f:
        records = pickle.load(f)
    with (p / "bm25.pkl").open("rb") as f:
        bm25 = pickle.load(f)
    with (p / "tokens.pkl").open("rb") as f:
        tokens = pickle.load(f)
    faiss_index = faiss.read_index(str(p / "faiss.index"))
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
