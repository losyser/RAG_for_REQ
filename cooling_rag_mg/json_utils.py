"""容错 JSON 解析：剥 markdown 围栏 / 抽取首个 JSON 对象。

LLM 即便被要求只输出 JSON，偶尔仍会包 ```json``` 围栏或夹叙述（实测 Kimi
会偶发围栏，导致 json.loads 直接失败）。集中在此处理，所有解析器复用。
"""
from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def loads_lenient(raw: str | None) -> dict[str, Any]:
    """尽力把 LLM 文本解析成 dict；彻底失败 → {}。"""
    if not raw:
        return {}
    text = _FENCE.sub("", raw.strip())
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass
    # 退路：抽取首个 {...} 块
    start, depth = text.find("{"), 0
    if start >= 0:
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        return obj if isinstance(obj, dict) else {}
                    except Exception:
                        break
    return {}
