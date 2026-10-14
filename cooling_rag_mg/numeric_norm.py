# cooling_rag_mg/numeric_norm.py
"""数值抽取与归一化：全角转半角，统一各种连字符，去掉多余的尾零。"""
from __future__ import annotations

import re
import unicodedata

_NUM = re.compile(r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)")  # 不能用 \w：中文字符属于 \w，会漏掉"高于85°C"


def _norm_num(s: str) -> str:
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def extract_numbers(s: str) -> list[str]:
    if not s:
        return []
    t = unicodedata.normalize("NFKC", str(s))
    t = re.sub(r"\{\{TBD[^}]*\}\}", " ", t)
    t = re.sub(r"[–—~～]", "-", t)
    return [_norm_num(m.group(1)) for m in _NUM.finditer(t)]
