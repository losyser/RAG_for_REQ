from __future__ import annotations

from pathlib import Path

from cooling_rag_mg.docx_parser import parse_evidence_docx
from cooling_rag_mg.granularity_builder import (
    build_evidence_units,
    build_source_chunks,
    build_evidence_groups,
    build_review_markdown,
)
from cooling_rag_mg.jsonl import write_jsonl


def convert_docx_to_multigranular(
    *,
    docx_path: str | Path,
    evidence_units_path: str | Path,
    source_chunks_path: str | Path,
    evidence_groups_path: str | Path,
    review_md_path: str | Path,
) -> dict[str, int]:
    raw_entries = parse_evidence_docx(docx_path)
    units = build_evidence_units(raw_entries)
    chunks = build_source_chunks(units)
    groups = build_evidence_groups(units)

    write_jsonl(evidence_units_path, units)
    write_jsonl(source_chunks_path, chunks)
    write_jsonl(evidence_groups_path, groups)

    review_md = build_review_markdown(raw_entries, units, chunks, groups)
    Path(review_md_path).parent.mkdir(parents=True, exist_ok=True)
    Path(review_md_path).write_text(review_md, encoding="utf-8")

    return {
        "raw_entries": len(raw_entries),
        "evidence_units": len(units),
        "source_chunks": len(chunks),
        "evidence_groups": len(groups),
    }
