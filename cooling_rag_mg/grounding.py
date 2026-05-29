from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from cooling_rag_mg.jsonl import read_jsonl


def load_evidence_text_map(units_path: str | Path) -> dict[str, str]:
    """evidence_id -> evidence text，来自 evidence_units.jsonl。"""
    return {u["id"]: (u.get("text") or "") for u in read_jsonl(units_path)}
