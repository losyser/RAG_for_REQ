from __future__ import annotations

from typing import Any


def rrf_fuse(result_lists: list[list[dict[str, Any]]], *, id_key: str = "id", k: int = 60) -> list[dict[str, Any]]:
    fused: dict[str, dict[str, Any]] = {}
    scores: dict[str, float] = {}

    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            rid = str(item.get(id_key) or item.get("chunk_id") or item.get("id"))
            if not rid:
                continue
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank)
            if rid not in fused:
                fused[rid] = dict(item)

    for rid, score in scores.items():
        fused[rid]["rrf_score"] = score

    return sorted(fused.values(), key=lambda x: x.get("rrf_score", 0.0), reverse=True)
