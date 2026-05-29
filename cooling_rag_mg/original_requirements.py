from __future__ import annotations

import json
from typing import Any

_GEN_SYSTEM = """你是船舶主机冷却水系统的资深需求工程师。请生成 {n} 条**高层运行需要**层级的原始干系人需求。
要求：
- 每条是利益相关方的**运行/性能需要**（高层），不是工程实现细节、不含具体数字阈值。
- 语言自然、贴近真实船东/轮机长/船检的口吻，难度与主题要有多样性。
- **不得照抄/复制**任何标准条文或证据库原文，只写需要、不写规范出处。
- 覆盖参考主题（可发散）：{topics}

只输出 JSON：{{"requirements":[{{"stakeholder":"...","requirement_text":"..."}}, ...]}}"""


def build_generation_prompt(n: int, seed_topics: list[str]) -> str:
    return _GEN_SYSTEM.format(n=n, topics="、".join(seed_topics))


def _char_ngrams(s: str, n: int = 4) -> set[str]:
    s = "".join(s.split())
    return {s[i:i + n] for i in range(max(len(s) - n + 1, 0))} or {s}


def _jaccard(a: str, b: str) -> float:
    A, B = _char_ngrams(a), _char_ngrams(b)
    return len(A & B) / len(A | B) if (A | B) else 0.0


def quality_check(reqs: list[dict], kb_texts: list[str], sim_threshold: float = 0.8) -> list[dict]:
    """对每条原始需求计算与 KB 文本的最大字符 n-gram Jaccard 相似度，
    超阈值则标记 kb_copy_suspect=True（防止原始需求照抄证据库原文）。"""
    out = []
    for r in reqs:
        text = r.get("requirement_text", "")
        max_sim = max((_jaccard(text, k) for k in kb_texts), default=0.0)
        out.append({
            "requirement_id": r["requirement_id"],
            "max_kb_similarity": round(max_sim, 3),
            "kb_copy_suspect": max_sim >= sim_threshold,
        })
    return out


def parse_generated(raw: str, start_index: int, prefix: str = "OR") -> list[dict[str, Any]]:
    data = json.loads(raw or "{}")
    out: list[dict[str, Any]] = []
    idx = start_index
    for item in data.get("requirements", []):
        text = (item.get("requirement_text") or "").strip()
        if not text:
            continue
        out.append({
            "requirement_id": f"{prefix}{idx:03d}",
            "stakeholder": (item.get("stakeholder") or "").strip(),
            "requirement_text": text,
        })
        idx += 1
    return out
