from __future__ import annotations

import json
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


_ENTAIL_PROMPT = """你是船舶冷却水系统的需求-证据核对专家。判断下面这条"证据"是否支持这条"工程需求(shall)"。
- support：证据直接给出该需求所需的参数、约束或规则依据。
- partial：证据与需求相关，但不足以直接支撑该义务。
- none：证据与需求无实质支撑关系。

工程需求(shall)：{shall}
证据：{evidence}

只输出 JSON，无解释：{{"verdict": "support" 或 "partial" 或 "none"}}"""

_VERDICT_SCORE = {"support": 1.0, "partial": 0.5, "none": 0.0}


class LLMEntailmentScorer:
    """用独立 LLM（Qwen/文心）判证据对 shall 的支持度 → 1.0/0.5/0.0。接口与 RerankerScorer 对齐。"""

    def __init__(self, client: Any, model: str, temperature: float = 0.0) -> None:
        self.client = client
        self.model = model
        self.temperature = temperature

    def _score_one(self, shall: str, evidence: str) -> float:
        from cooling_rag_mg.llm_cache import cached_completion
        try:
            resp = cached_completion(
                self.client,
                model=self.model,
                messages=[{"role": "user", "content": _ENTAIL_PROMPT.format(shall=shall, evidence=evidence)}],
                temperature=self.temperature,
                max_tokens=50,
                response_format={"type": "json_object"},
            )
            obj = json.loads(resp.choices[0].message.content or "{}")
            return _VERDICT_SCORE.get(str(obj.get("verdict", "")).strip().lower(), 0.0)
        except Exception:
            return 0.0

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [self._score_one(shall, ev) for shall, ev in pairs]


def score_result_sets(
    result_sets: list[dict[str, Any]],
    text_map: dict[str, str],
    scorer: Any,
) -> dict[str, float]:
    """返回 {source_requirement_id: 该 source req 下所有有证据 ER 的 grounding 分均值}。"""
    by_src: dict[str, list[float]] = {}
    for src, shall, ev_ids in iter_grounded_ers(result_sets):
        ev_texts = [text_map.get(e, "") for e in ev_ids]
        er_score = mean_pair_score(scorer, shall, ev_texts)
        by_src.setdefault(src, []).append(er_score)
    return {src: float(sum(v) / len(v)) for src, v in by_src.items() if v}


def paired_compare(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    *,
    n_boot: int = 10000,
    seed: int = 42,
) -> dict[str, float]:
    """在两个 {key: score} 的交集 key 上配对比较。返回 mean、配对 Wilcoxon p、bootstrap 均值差 CI。"""
    import numpy as np
    from scipy import stats

    keys = sorted(set(scores_a) & set(scores_b))
    a = np.array([scores_a[k] for k in keys], dtype=float)
    b = np.array([scores_b[k] for k in keys], dtype=float)
    n = len(keys)

    if n == 0:
        return {"n_pairs": 0, "mean_a": float("nan"), "mean_b": float("nan"),
                "mean_diff": float("nan"), "pvalue": float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan")}

    diff = a - b
    if n < 2 or np.allclose(diff, 0.0):
        pvalue = 1.0
    else:
        pvalue = float(stats.wilcoxon(a, b, zero_method="wilcox",
                                      correction=False, alternative="two-sided").pvalue)

    rng = np.random.default_rng(seed)
    boots = np.array([rng.choice(diff, size=n, replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])

    return {
        "n_pairs": n,
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "mean_diff": float(diff.mean()),
        "pvalue": pvalue,
        "ci_low": float(lo),
        "ci_high": float(hi),
    }
