from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from cooling_rag_mg.jsonl import read_jsonl


def load_evidence_text_map(units_path: str | Path) -> dict[str, str]:
    """evidence_id -> evidence text，来自 evidence_units.jsonl。"""
    return {u["id"]: (u.get("text") or "") for u in read_jsonl(units_path)}


def iter_grounded_ers(
    result_sets: list[dict[str, Any]],
) -> Iterator[tuple[str, str, list[str]]]:
    """产出 (source_requirement_id, shall_statement, evidence_ids)，仅限二者皆非空的 ER。"""
    for rs in result_sets:
        src = str(rs.get("source_requirement_id") or "")
        for er in rs.get("engineering_requirements") or []:
            ev = [e for e in (er.get("evidence_ids") or []) if e]
            shall = (er.get("shall_statement") or "").strip()
            if ev and shall:
                yield src, shall, ev
