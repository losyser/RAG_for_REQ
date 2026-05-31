"""盲评两两对比的共识聚合 + 描述性指标（v2 Task 7）。

- consensus_pair：对同一对 (R, B0) 跑两次盲评（左右交换），逐维取共识；两次不一致
  即判定为受位置影响 → tie，并标记位置偏置，杜绝"裁判只是偏左/偏右"的假胜。
- aggregate_quality：把每源的共识行汇总成各维 R/B0/tie 计数 + 总体胜负。
- 描述性指标：可溯源率、shall 含具体数字占比（与生成质量正交，只描述风格）。
"""
from __future__ import annotations

import re
from typing import Any

from cooling_rag_mg.quality_judge import DIMS, judge_pair


def consensus_pair(requirement_text: str, r_text: str, b0_text: str,
                   client: Any, model: str, temperature: float = 0.0) -> tuple[dict, dict]:
    """跑两次盲评（R 分别放左、放右），逐维取共识。

    返回 (consensus, biased)：consensus[dim] ∈ {'R','B0','tie'}（两次不一致→'tie'）；
    biased[dim] = 两次判定是否不一致（True 表示该维受位置影响，已被降为 tie）。"""
    left = judge_pair(requirement_text, r_text, b0_text, r_on_left=True, client=client,
                      model=model, temperature=temperature)
    right = judge_pair(requirement_text, r_text, b0_text, r_on_left=False, client=client,
                       model=model, temperature=temperature)
    consensus, biased = {}, {}
    for d in DIMS:
        agree = left[d] == right[d]
        consensus[d] = left[d] if agree else "tie"
        biased[d] = not agree
    return consensus, biased


def aggregate_quality(rows: list[dict]) -> dict:
    """把每源共识行汇总成各维 {R,B0,tie} 计数，外加 overall（四维合计）。"""
    out: dict[str, dict] = {d: {"R": 0, "B0": 0, "tie": 0} for d in DIMS}
    overall = {"R": 0, "B0": 0, "tie": 0}
    for row in rows:
        for d in DIMS:
            v = row.get(d, "tie")
            v = v if v in ("R", "B0", "tie") else "tie"
            out[d][v] += 1
            overall[v] += 1
    out["overall"] = overall
    return out


def numeric_fraction(ers: list[dict]) -> float:
    """含具体数字的 shall 占比（描述风格，非质量评判）。无 shall → 0.0。"""
    txt = [str(e.get("shall_statement", "")) for e in ers if isinstance(e, dict)]
    txt = [t for t in txt if t.strip()]
    if not txt:
        return 0.0
    return sum(1 for t in txt if re.search(r"\d", t)) / len(txt)


def traceability_rate(ers: list[dict]) -> float:
    """带非空 evidence_ids 的 shall 占比（仅描述，刻意不进质量鱼骨以免天然偏 RAG）。"""
    items = [e for e in ers if isinstance(e, dict) and str(e.get("shall_statement", "")).strip()]
    if not items:
        return 0.0
    return sum(1 for e in items if e.get("evidence_ids")) / len(items)
