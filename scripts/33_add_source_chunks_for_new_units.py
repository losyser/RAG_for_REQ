# -*- coding: utf-8 -*-
"""
Create source_chunk entries for all new evidence units (S60-S69)
that currently have no parent in source_chunks.jsonl.

Each new source document gets one synthetic source_chunk whose
evidence_ids list contains all child evidence_unit ids from that document.
Then rebuild the source_chunks index.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

EU_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl"
SC_PATH = PROJECT_ROOT / "data" / "processed" / "source_chunks.jsonl"


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    with open(EU_PATH, encoding="utf-8") as f:
        units = [json.loads(l) for l in f if l.strip()]

    with open(SC_PATH, encoding="utf-8") as f:
        chunks = [json.loads(l) for l in f if l.strip()]

    existing_chunk_ids = {c["chunk_id"] for c in chunks}

    # Collect new units whose parent_chunk_id is missing
    orphans: dict[str, list[dict]] = defaultdict(list)
    for u in units:
        pid = u["parent_chunk_id"]
        if pid not in existing_chunk_ids:
            orphans[pid].append(u)

    print(f"Orphan parent_chunk_ids: {len(orphans)}")
    for pid, eu_list in sorted(orphans.items()):
        print(f"  {pid}  ({len(eu_list)} units)")

    # Build one synthetic source_chunk per orphan parent_chunk_id
    new_chunks = []
    for pid, eu_list in orphans.items():
        # Aggregate metadata from child units
        rep = eu_list[0]  # use first child as representative
        m = rep["metadata"]

        # Combined text = topic + all child texts joined
        combined_text = "\n\n".join(
            f"{u['metadata'].get('topic','')}\n{u['text']}"
            for u in eu_list
        )

        # Build search_text
        all_can_support = sorted({a for u in eu_list for a in (u["metadata"].get("can_support") or [])})
        all_components = sorted({c for u in eu_list for c in (u["metadata"].get("component_objects") or [])})
        all_phases = sorted({p for u in eu_list for p in (u["metadata"].get("engineering_phase") or [])})

        search_parts = [
            m.get("source_document", ""),
            m.get("source_type", ""),
            " ".join(all_components),
            " ".join(all_can_support),
            " ".join(all_phases),
            combined_text[:300],
        ]

        chunk = {
            "chunk_id": pid,
            "chunk_text": combined_text,
            "search_text": "\n".join(p for p in search_parts if p),
            "evidence_ids": [u["id"] for u in eu_list],
            "metadata": {
                "source_document": m.get("source_document", ""),
                "location": "",
                "section_title": m.get("topic", ""),
                "source_types": [m.get("source_type", "")],
                "source_type": m.get("source_type", ""),
                "applicability_level": m.get("applicability_level", "general"),
                "is_generalizable": m.get("is_generalizable", "general"),
                "system_scope": all_components,
                "component_objects": all_components,
                "evidence_types": all_can_support,
                "requirement_intents": all_can_support,
                "engineering_phase": all_phases,
                "applicable_condition": ["normal_operation"],
                "can_support": all_can_support,
                "evidence_strength": m.get("evidence_strength", "direct"),
            },
        }
        new_chunks.append(chunk)

    print(f"\nCreating {len(new_chunks)} new source_chunks")

    # Update parent_chunk_id in evidence_units to match (already correct)
    # Just verify they match
    all_new_pids = {c["chunk_id"] for c in new_chunks}
    for u in units:
        if u["parent_chunk_id"] in all_new_pids:
            pass  # already correct

    # Write updated source_chunks.jsonl
    merged = chunks + new_chunks
    with open(SC_PATH, "w", encoding="utf-8") as f:
        for c in merged:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"source_chunks.jsonl: {len(chunks)} → {len(merged)}")

    # Rebuild source_chunks index
    print("\nRebuilding source_chunks index…")
    from cooling_rag_mg.config import get_config
    from cooling_rag_mg.index_store import build_index
    cfg = get_config()
    build_index(
        jsonl_path=cfg.paths.source_chunks_jsonl,
        output_dir=cfg.paths.indexes_dir / "source_chunks",
        text_field="search_text",
        model_path=cfg.model.embedding_model_path,
        device=cfg.model.device,
        normalize=cfg.model.normalize_embeddings,
    )
    print("Done.")


if __name__ == "__main__":
    main()
