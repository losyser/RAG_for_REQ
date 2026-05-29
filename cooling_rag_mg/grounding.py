from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from cooling_rag_mg.jsonl import read_jsonl


def load_evidence_text_map(units_path: str | Path) -> dict[str, str]:
    """evidence_id -> evidence text，来自 evidence_units.jsonl。"""
    return {u["id"]: (u.get("text") or "") for u in read_jsonl(units_path)}


def iter_grounded_ers(
    result_sets: list[dict[str, Any]],
) -> Iterator[tuple[str, str, list[str]]]:
    """产出 (source_requirement_id, shall_statement, evidence_ids)，仅限二者皆非空的 ER。"""
    for rs in result_sets:
        src = str(rs.get("source_requirement_id") or "")
        for er in rs.get("engineering_requirements") or []:
            ev = [e for e in (er.get("evidence_ids") or []) if e]
            shall = (er.get("shall_statement") or "").strip()
            if ev and shall:
                yield src, shall, ev


class RerankerScorer:
    """CrossEncoder 包装，输出 (query, passage) 相关性分。独立于检索所用的 BGE-M3 dense 信号。"""

    def __init__(self, model_path: str = "BAAI/bge-reranker-v2-m3", device: str = "cpu") -> None:
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_path, device=device)

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        return [float(s) for s in self.model.predict(pairs)]


def mean_pair_score(scorer: Any, shall: str, evidence_texts: list[str]) -> float:
    """一条 ER 的 grounding 分 = 其所有 (shall, evidence) 对得分的均值。"""
    pairs = [(shall, ev) for ev in evidence_texts if ev]
    if not pairs:
        return 0.0
    scores = scorer.score_pairs(pairs)
    return float(sum(scores) / len(scores)) if scores else 0.0
