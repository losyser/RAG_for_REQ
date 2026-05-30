"""覆盖率优先的多查询检索：对多条 query 各自 vector+bm25+rrf，按 id 取并集去重。

精准的活交给生成端（据证据生成时再判相关性），这里只管把覆盖率拉高。
真实 searcher 用 HybridIndexSearcher(load_index(indexes_dir/'evidence_units'), device=...)。
"""
from __future__ import annotations

from typing import Any

from cooling_rag_mg.hybrid_fusion import rrf_fuse


def coverage_retrieve(queries: list[str], searcher: Any, per_query_k: int = 20, max_total: int = 60) -> list[dict]:
    """多 query 各自 vector+bm25+rrf 后按 id 取并集去重（保留首次出现），上限 max_total。"""
    seen: dict[str, dict] = {}
    for q in queries:
        vec = searcher.vector_search(q, per_query_k)
        bm = searcher.bm25_search(q, per_query_k)
        for cand in rrf_fuse([vec, bm]):
            cid = cand.get("id") or cand.get("chunk_id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                break
    return list(seen.values())
