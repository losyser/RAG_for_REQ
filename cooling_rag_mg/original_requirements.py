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
