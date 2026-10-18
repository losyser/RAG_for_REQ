"""证据检索：覆盖率优先（旧接口）+ 元数据对齐精准检索（新接口）。

aligned_retrieve（推荐）：
  1. 调用 requirement_analyzer 从需求文本提取 (component, intent) 对
  2. 对每对做 filtered_vector_search + filtered_bm25_search + RRF
  3. 并集去重，返回精准候选集

coverage_retrieve（旧接口，保留兼容）：
  对多条 query 各自 vector+bm25+rrf，只管覆盖率不管精准度。
"""
from __future__ import annotations

from typing import Any

from cooling_rag_mg.hybrid_fusion import rrf_fuse


def coverage_retrieve(
    queries: list[str],
    searcher: Any,
    per_query_k: int = 20,
    max_total: int = 60,
) -> list[dict]:
    """旧接口：多 query 各自 vector+bm25+rrf 后按 id 取并集去重，上限 max_total。"""
    seen: dict[str, dict] = {}
    for q in queries:
        vec = searcher.vector_search(q, per_query_k)
        bm  = searcher.bm25_search(q, per_query_k)
        for cand in rrf_fuse([vec, bm]):
            cid = cand.get("id") or cand.get("chunk_id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                break
    return list(seen.values())


def aligned_retrieve(
    requirement_text: str,
    searcher: Any,
    analyzer_client: Any,
    analyzer_model: str,
    *,
    per_pair_k: int = 8,
    max_total: int = 30,
    fallback_k: int = 15,
    timing: dict | None = None,
    diagnostics: dict | None = None,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """元数据对齐的精准检索。

    Parameters
    ----------
    requirement_text:  原始需求文本
    searcher:          HybridIndexSearcher（索引含 primary_component/intent 字段）
    analyzer_client:   OpenAI-compatible client（用于 requirement_analyzer）
    analyzer_model:    模型名
    per_pair_k:        每个 (component, intent) 对各取多少条候选（vector+bm25 各取）
    max_total:         并集上限
    fallback_k:        若 analyzer 返回空则 fallback 到无过滤检索取多少条

    Returns
    -------
    (evidence_list, pairs_used)
      evidence_list: 去重后的证据字典列表，按 RRF 顺序
      pairs_used:    实际用到的 (component, intent) 对列表（空=fallback）
    """
    if min(per_pair_k, max_total, fallback_k) < 1:
        raise ValueError("retrieval limits must be positive")
    from cooling_rag_mg.requirement_analyzer import analyze_requirement

    import time as _t
    _t0 = _t.perf_counter()
    pairs = analyze_requirement(requirement_text, analyzer_client, analyzer_model)
    _t1 = _t.perf_counter()
    if timing is not None:
        timing["stage1_s"] = round(_t1 - _t0, 3)

    processed_pairs = []
    def _done(result):
        if diagnostics is not None:
            diagnostics.update({"policy": "existing_hard_pair_filter", "mapping_correctness": "unknown",
                "pairs_used": [list(p) for p in pairs], "processed_pairs": processed_pairs,
                "unfiltered_fallback_used": not bool(pairs), "result_count": len(result[0]),
                "nonempty_mapping_zero_results": bool(pairs) and not bool(result[0]),
                "unfiltered_rescue_attempted": False, "recall": "unknown"})
        if timing is not None:
            timing["retrieval_s"] = round(_t.perf_counter() - _t1, 3)
        return result

    if not pairs:
        # fallback：退化为无过滤的单条查询
        vec = searcher.vector_search(requirement_text, fallback_k)
        bm  = searcher.bm25_search(requirement_text, fallback_k)
        candidates = {
            (r.get("id") or r.get("chunk_id")): r
            for r in rrf_fuse([vec, bm])
            if r.get("id") or r.get("chunk_id")
        }
        return _done((list(candidates.values())[:max_total], []))

    seen: dict[str, dict] = {}
    for comp, intent in pairs:
        vec = searcher.filtered_vector_search(
            requirement_text, per_pair_k,
            components=[comp], intents=[intent],
        )
        bm = searcher.filtered_bm25_search(
            requirement_text, per_pair_k,
            components=[comp], intents=[intent],
        )
        if diagnostics is not None:
            processed_pairs.append({"component": comp, "intent": intent, "vector_count": len(vec), "bm25_count": len(bm)})
        for cand in rrf_fuse([vec, bm]):
            cid = cand.get("id") or cand.get("chunk_id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                return _done((list(seen.values()), pairs))

    return _done((list(seen.values()), pairs))
