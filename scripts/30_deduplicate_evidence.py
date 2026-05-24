# -*- coding: utf-8 -*-
"""
Deduplicate evidence_units.jsonl by text fingerprint.

Strategy:
- Group units whose first 400 normalised characters are identical (MD5 hash).
- Within each group keep the single best representative:
    1. Prefer 'direct' evidence_strength over 'indirect'
    2. Then prefer larger can_support list
    3. Then prefer larger text length
- Write deduplicated JSONL; backup original.
- Report statistics.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JSONL_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl"
BACKUP_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl.bak"


def _fp(text: str) -> str:
    normalised = text[:400].lower().strip()
    return hashlib.md5(normalised.encode("utf-8", errors="replace")).hexdigest()


def _score(unit: dict) -> tuple:
    m = unit.get("metadata", {})
    strength = 0 if m.get("evidence_strength") == "direct" else 1
    support_len = -len(m.get("can_support") or [])
    text_len = -len(unit.get("text", ""))
    return (strength, support_len, text_len)


def main() -> None:
    with open(JSONL_PATH, encoding="utf-8") as f:
        units = [json.loads(l) for l in f if l.strip()]

    print(f"Loaded {len(units)} evidence units")

    groups: dict[str, list[dict]] = {}
    for u in units:
        key = _fp(u["text"])
        groups.setdefault(key, []).append(u)

    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Duplicate text groups: {len(dup_groups)}")
    print(f"Units in duplicate groups: {sum(len(v) for v in dup_groups.values())}")

    # Keep best representative per group
    deduped: list[dict] = []
    seen_ids: set[str] = set()
    removed = 0
    for key, group in groups.items():
        best = min(group, key=_score)
        # Ensure unique ID (if ID itself is duplicated, suffix it)
        uid = best["id"]
        if uid in seen_ids:
            uid = f"{uid}_dup{removed}"
            best = dict(best)
            best["id"] = uid
        seen_ids.add(uid)
        deduped.append(best)
        removed += len(group) - 1

    print(f"\nRemoved {removed} duplicate units")
    print(f"Output: {len(deduped)} evidence units")

    # Backup original
    shutil.copy2(JSONL_PATH, BACKUP_PATH)
    print(f"Original backed up to: {BACKUP_PATH}")

    # Write deduplicated file
    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        for u in deduped:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    print(f"Written: {JSONL_PATH}")

    # Report aspect coverage after dedup
    import collections
    aspect_counter: dict[str, int] = collections.Counter()
    for u in deduped:
        for a in (u["metadata"].get("can_support") or []):
            aspect_counter[a] += 1
    print("\nAspect coverage after dedup:")
    for k, v in sorted(aspect_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")


if __name__ == "__main__":
    main()
