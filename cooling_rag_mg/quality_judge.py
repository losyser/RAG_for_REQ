"""盲评两两对比质量裁判（Qwen，跨 DeepSeek 生成者）。

同一原始需求下，R 与 B0 两份工程需求匿名打乱（左右交换）交裁判逐维判 A/B/tie，
再归一到 R 视角（'R'/'B0'/'tie'）。维度刻意不含"是否带引用/可溯源"以免天然偏 RAG。
"""
from __future__ import annotations

import json
from typing import Any

DIMS = ["completeness", "actionability", "consistency", "verifiability"]

_PROMPT = """你是船舶冷却水系统资深评审。下面是同一原始需求的两份工程需求方案 A 和 B。
就每个维度判断哪份更好：完整性 completeness、具体可操作性 actionability、内部一致性 consistency、可验证性 verifiability。
不要因为某份"带证据引用"而偏向它，只看工程需求本身质量。
原始需求：{req}
方案A：{a}
方案B：{b}
只输出 JSON：{{"completeness":"A|B|tie","actionability":"A|B|tie","consistency":"A|B|tie","verifiability":"A|B|tie"}}"""


def parse_pairwise(raw: str) -> dict:
    try:
        obj = json.loads(raw or "{}")
    except Exception:
        return {d: "tie" for d in DIMS}
    out = {}
    for d in DIMS:
        v = str(obj.get(d, "tie")).strip().upper()
        out[d] = v if v in {"A", "B"} else "tie"
    return out


def judge_pair(requirement_text: str, r_text: str, b0_text: str, r_on_left: bool,
               client: Any, model: str, temperature: float = 0.0) -> dict:
    """R vs B0 盲评。r_on_left 决定 R 放 A 位(True) 还是 B 位。返回每维 'R'/'B0'/'tie'。"""
    from cooling_rag_mg.llm_cache import cached_completion
    a, b = (r_text, b0_text) if r_on_left else (b0_text, r_text)
    try:
        resp = cached_completion(
            client, model=model,
            messages=[{"role": "user", "content": _PROMPT.format(req=requirement_text, a=a, b=b)}],
            temperature=temperature, max_tokens=200, response_format={"type": "json_object"},
        )
        raw = parse_pairwise(resp.choices[0].message.content or "{}")
    except Exception:
        raw = {d: "tie" for d in DIMS}

    def norm(v: str) -> str:
        if v == "tie":
            return "tie"
        win_is_left = (v == "A")
        return "R" if (win_is_left == r_on_left) else "B0"

    return {d: norm(raw[d]) for d in DIMS}
