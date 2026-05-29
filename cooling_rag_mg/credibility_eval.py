"""公平可信度评估层（Phase 2）。

把每条 shall 的事实 claim 抽出，逐条对 KB 回溯判定 support/contradict/not_found，
得到硬幻觉(H_hard=contradict)、软幻觉(H_soft=not_found)、过推断(OI)。两组(B0/R)用
同一套判法，破除 M1 无证据率的循环。详见 spec 2026-05-30-rag-credibility-replan-design.md。
"""
from __future__ import annotations

import json
from typing import Any, Callable

_CLAIM_PROMPT = """从下面这条工程需求(shall)中抽取所有**原子事实性 claim**（具体参数、阈值、标准引用、设计规则）。
不要抽取空泛的意图。只输出 JSON：{{"claims":["...", ...]}}
工程需求：{shall}"""


def extract_claims(shall: str, client: Any, model: str, temperature: float = 0.0) -> list[str]:
    """用 LLM 从 shall 抽取原子事实性 claim 列表。失败/空 → []。"""
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(
            client, model=model,
            messages=[{"role": "user", "content": _CLAIM_PROMPT.format(shall=shall)}],
            temperature=temperature, max_tokens=400,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        claims = json.loads(content or "{}").get("claims", [])
        return [str(c).strip() for c in claims if str(c).strip()]
    except Exception:
        return []


def verify_claim_against_kb(
    claim: str,
    kb_search: Callable[[str, int], list[str]],
    judge: Callable[[str, list[str]], str],
    top_k: int = 5,
) -> str:
    """对单条 claim 做 KB 回溯判定，返回 'support' | 'contradict' | 'not_found'。

    kb_search(claim, top_k) -> 召回的 KB 段落文本列表（空 → not_found，无从核验）。
    judge(claim, passages) -> verdict；非法 verdict 归一为 not_found。
    两组用同一套 kb_search+judge，保证公平、非循环。"""
    passages = kb_search(claim, top_k)
    if not passages:
        return "not_found"
    verdict = judge(claim, passages)
    return verdict if verdict in {"support", "contradict", "not_found"} else "not_found"


def score_shall(
    shall: str,
    extract: Callable[[str], list[str]],
    verify: Callable[[str], str],
) -> dict[str, Any]:
    """一条 shall 的可信度打分。

    extract: shall -> list[claim]；verify: claim -> verdict。
    H_hard=contradict 占比，H_soft=not_found 占比，hallucination=两者之和。
    无 claim → 各比率为 None（该 shall 不计入幻觉率均值，避免把『无可核验事实』当 0 偏置）。"""
    claims = extract(shall)
    n = len(claims)
    if n == 0:
        return {"n_claims": 0, "h_hard": None, "h_soft": None, "hallucination": None}
    verdicts = [verify(c) for c in claims]
    hard = sum(1 for v in verdicts if v == "contradict") / n
    soft = sum(1 for v in verdicts if v == "not_found") / n
    return {"n_claims": n, "h_hard": hard, "h_soft": soft, "hallucination": hard + soft}
