# cooling_rag_mg/retrieval_variants.py
"""E3 用到的检索变体（只给定 pairs 做检索，不调 LLM），以及切分边界分析。"""
from __future__ import annotations

import re
from typing import Any

from cooling_rag_mg.hybrid_fusion import rrf_fuse

_COND = re.compile(r"(当|若|如果|除|但|否则|在.{0,8}时|以下|以上|unless|except|where|when|if|provided that|in case)", re.I)
_VAL = re.compile(r"\d+(?:\.\d+)?\s*(?:°C|℃|MPa|bar|kPa|%|s\b|秒|min|分钟|m³/h|L/min|rpm|kW|mm)")
_SENT = re.compile(r"[^。；;.\n]+[。；;.\n]?")


def retrieve_for_pairs(text: str, pairs: list[tuple[str, str]], searcher: Any, *, mode: str = "hybrid",
                       per_pair_k: int = 8, k0: int = 60, w_bm25: float = 0.5,
                       max_total: int = 20) -> list[dict]:
    seen: dict[str, dict] = {}
    for comp, intent in pairs:
        vec = searcher.filtered_vector_search(text, per_pair_k, components=[comp], intents=[intent]) \
            if mode in ("hybrid", "vector") else []
        bm = searcher.filtered_bm25_search(text, per_pair_k, components=[comp], intents=[intent]) \
            if mode in ("hybrid", "bm25") else []
        lists = [l for l in (vec, bm) if l]
        if mode == "hybrid":
            ranked = rrf_fuse([vec, bm], k=k0, weights=[2 * (1 - w_bm25), 2 * w_bm25])
        else:
            ranked = rrf_fuse(lists, k=k0)
        for cand in ranked:
            cid = cand.get("id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                return list(seen.values())
    return list(seen.values())


def boundary_split_rate(texts: list[str], window: int, overlap: float) -> dict:
    """统计"同时含条件词和数值阈值的句子"中，有多少句没有被任何一个固定窗口完整覆盖。"""
    step = max(1, int(window * (1 - overlap)))
    n = split = 0
    for t in texts:
        starts = list(range(0, max(1, len(t) - window + 1), step)) or [0]
        if starts[-1] + window < len(t):
            starts.append(len(t) - window)
        for m in _SENT.finditer(t):
            s = m.group(0)
            if not (_COND.search(s) and _VAL.search(s)):
                continue
            n += 1
            a, b = m.start(), m.end()
            if not any(st_ <= a and b <= st_ + window for st_ in starts):
                split += 1
    return {"window": window, "overlap": overlap, "n_condition_value_sentences": n,
            "split_pct": round(split / n * 100, 1) if n else None}
