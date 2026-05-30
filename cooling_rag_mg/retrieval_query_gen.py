"""Kimi 由原始需求生成检索内容（关键词 + 中/英检索句），覆盖率优先。

多智能体分工中的「检索内容生成」角色（Kimi/Moonshot），仅 RAG 产线使用。
"""
from __future__ import annotations

from typing import Any

from cooling_rag_mg.json_utils import loads_lenient

_QUERY_PROMPT = """你是船舶冷却水系统检索助手。针对下面的原始需求，生成用于在中英文混合文档库中**检索证据**的内容，追求覆盖率。
- keywords：组成对象/部件/工程方面等关键词（中文和英文都给）。
- sentences：适合语义检索的完整句子（中文和英文都给）。
只输出 JSON：{{"keywords":["..."],"sentences":["..."]}}
原始需求：{req}"""


def build_query_prompt(requirement_text: str) -> str:
    return _QUERY_PROMPT.format(req=requirement_text)


def parse_queries(raw: str) -> list[str]:
    """把 keywords + sentences 合并成去重的检索查询列表。解析失败 → []。"""
    obj = loads_lenient(raw)
    out: list[str] = []
    for key in ("keywords", "sentences"):
        for x in obj.get(key, []) or []:
            s = str(x).strip()
            if s and s not in out:
                out.append(s)
    return out


def generate_queries(requirement_text: str, client: Any, model: str, temperature: float = 0.3) -> list[str]:
    """调 Kimi 生成检索内容并解析为查询列表。失败 → []。"""
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(
            client, model=model,
            messages=[{"role": "user", "content": build_query_prompt(requirement_text)}],
            temperature=temperature, max_tokens=500, response_format={"type": "json_object"},
        )
        return parse_queries(resp.choices[0].message.content or "{}")
    except Exception:
        return []
