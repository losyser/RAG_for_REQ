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

_OI_PROMPT = """你是船舶冷却水系统的需求审查专家。判断这条工程需求(shall)是否**过度推断**：
即它是否添加了**原始需求与证据都未授权**的义务/约束（范围蔓延），而非忠实落实原始需求。
注意：与事实对错无关，只看是否凭空扩大了范围/义务。

原始需求：{source}
证据：{evidence}
工程需求(shall)：{shall}

只输出 JSON：{{"over_inference": true 或 false}}"""


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


def judge_over_inference(
    shall: str,
    source_requirement: str,
    kb_passages: list[str],
    client: Any,
    model: str,
    temperature: float = 0.0,
) -> bool | None:
    """判断 shall 是否过度推断（超出原始需求+证据授权范围加义务）。

    成功 → True/False；调用失败/空/不可解析 → None（从过推断率均值剔除，不向下偏置）。
    与 H（事实对错）正交：OI 只看范围蔓延。"""
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(
            client, model=model,
            messages=[{"role": "user", "content": _OI_PROMPT.format(
                source=source_requirement, evidence="\n".join(kb_passages), shall=shall)}],
            temperature=temperature, max_tokens=50,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        if not content or not content.strip():
            return None
        val = json.loads(content).get("over_inference")
        return bool(val) if isinstance(val, bool) else None
    except Exception:
        return None


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
