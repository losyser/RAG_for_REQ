from __future__ import annotations

import re
from typing import Any


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def split_csv(value: Any) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    parts = re.split(r"[,，;；]\s*", text)
    return [p.strip() for p in parts if p.strip()]


def normalize_bool(value: Any) -> bool:
    text = safe_text(value).lower()
    return text in {"true", "1", "yes", "y", "是"}


def normalize_id(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z_\-]+", "_", text).strip("_")


def truncate(text: str, max_len: int = 1200) -> str:
    text = safe_text(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def simple_tokens(text: str) -> list[str]:
    text = safe_text(text).lower()
    zh = re.findall(r"[\u4e00-\u9fff]", text)
    en = re.findall(r"[a-z0-9_\-/\.]+", text)
    bigrams = ["".join(zh[i:i+2]) for i in range(len(zh)-1)]
    trigrams = ["".join(zh[i:i+3]) for i in range(len(zh)-2)]
    return en + bigrams + trigrams
