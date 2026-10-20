# scripts/105_regrade_existing.py
"""用审计后的 KB 重新分级审计前的结果（不调 API），量化审计的影响。"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import classify_result_set

ARCH = ROOT / "data/search_results/_archive_preaudit_20261014/exp_v4"
KB = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OUT = ROOT / "data/search_results/exp_v4/regrade_preaudit_with_v3kb.json"


def main() -> None:
    kb = {json.loads(l)["id"]: json.loads(l) for l in KB.open(encoding="utf-8")}
    res = {}
    for name in ("rag_v4_results.json", "norag_v4_results.json"):
        d = json.loads((ARCH / name).read_text(encoding="utf-8"))
        old = Counter(e["_grade"] for rs in d["result_sets"] for e in rs["engineering_requirements"])
        new = Counter(e["_grade"] for rs in d["result_sets"]
                      for e in classify_result_set(rs, kb)["engineering_requirements"])
        res[name] = {"old": dict(old), "new_with_v3kb": dict(new)}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
