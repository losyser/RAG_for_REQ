# scripts/95_apply_kb_audit.py
"""按审计表生成 evidence_units_v3_audited.jsonl。decision 为空则报错退出。"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.kb_provenance import provenance_group

KB_IN = ROOT / "data/processed/evidence_units_v2.jsonl"
AUDIT = ROOT / "data/processed/kb_audit/kb_provenance_audit.csv"
KB_OUT = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
SUMMARY = ROOT / "data/processed/kb_audit/kb_audit_summary.json"
VALID = {"KEEP", "DROP", "RETIER_L2", "RETIER_L3", "FIX_SOURCE"}


def main() -> None:
    rows = {r["id"]: r for r in csv.DictReader(AUDIT.open(encoding="utf-8-sig"))}
    units = [json.loads(l) for l in KB_IN.open(encoding="utf-8")]
    missing = [u["id"] for u in units if u["id"] not in rows]
    bad = [i for i, r in rows.items() if r["decision"] not in VALID]
    if missing or bad:
        sys.exit(f"audit incomplete: missing={missing[:5]} bad_decision={bad[:5]}")
    out, dec = [], Counter()
    for u in units:
        r = rows[u["id"]]
        d = r["decision"]
        dec[d] += 1
        if d == "DROP":
            continue
        u = json.loads(json.dumps(u))
        meta = u.setdefault("metadata", {})
        if d == "RETIER_L2":
            u["kb_tier"], u["tier_reason"] = "L2", "audit-2026-10: non-regulatory source"
        elif d == "RETIER_L3":
            u["kb_tier"], u["tier_reason"] = "L3", "audit-2026-10: operational/industry reference"
        elif d == "FIX_SOURCE":
            meta["source_document"] = r["corrected_source"] or meta.get("source_document", "")
            meta["location"] = r["corrected_location"] or meta.get("location", "")
        meta["provenance_group"] = provenance_group(u)
        meta["audit_decision"] = d
        out.append(u)
    with KB_OUT.open("w", encoding="utf-8") as f:
        for u in out:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    summary = {
        "n_before": len(units), "n_after": len(out), "by_decision": dict(dec),
        "tier_before": dict(Counter(u["kb_tier"] for u in units)),
        "tier_after": dict(Counter(u["kb_tier"] for u in out)),
        "sources_after": len({(u.get("metadata") or {}).get("source_document") for u in out}),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
