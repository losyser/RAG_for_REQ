# scripts/94_kb_provenance_audit.py
"""生成 KB 出处审计表 data/processed/kb_audit/kb_provenance_audit.csv。

spotcheck=1 标记需要抽样核对原文的保留单元：每份法规类文档（ORIG 组 L1、CCS2025）抽 3 条，SEED=42。
用法：PY scripts/94_kb_provenance_audit.py
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cooling_rag_mg.kb_provenance import audit_flags, proposed_action, provenance_group, source_document

KB = ROOT / "data/processed/evidence_units_v2.jsonl"
OUT_DIR = ROOT / "data/processed/kb_audit"
OUT = OUT_DIR / "kb_provenance_audit.csv"
COLS = ["id", "group", "kb_tier", "source_type", "source_document", "location", "flags",
        "proposed_action", "spotcheck", "decision", "corrected_source", "corrected_location",
        "evidence_of_verification", "text_snippet"]


def main() -> None:
    units = [json.loads(l) for l in KB.open(encoding="utf-8")]
    rng = random.Random(42)
    by_doc: dict[str, list[str]] = defaultdict(list)
    for u in units:
        if proposed_action(u) == "KEEP" and u.get("kb_tier") == "L1":
            by_doc[source_document(u)].append(u["id"])
    spot = {i for ids in by_doc.values() for i in rng.sample(sorted(ids), min(3, len(ids)))}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for u in units:
            meta = u.get("metadata") or {}
            act = proposed_action(u)
            w.writerow({
                "id": u["id"], "group": provenance_group(u), "kb_tier": u.get("kb_tier"),
                "source_type": meta.get("source_type", ""), "source_document": source_document(u),
                "location": meta.get("location", ""), "flags": ";".join(audit_flags(u)),
                "proposed_action": act, "spotcheck": int(u["id"] in spot),
                "decision": "" if act == "VERIFY" or u["id"] in spot else act,
                "corrected_source": "", "corrected_location": "", "evidence_of_verification": "",
                "text_snippet": (u.get("text") or "")[:300].replace("\n", " "),
            })
    acts = Counter(proposed_action(u) for u in units)
    print("units:", len(units), "| proposed:", dict(acts), "| spotcheck:", len(spot))
    print("written:", OUT)


if __name__ == "__main__":
    main()
