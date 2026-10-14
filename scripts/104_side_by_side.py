# scripts/104_side_by_side.py
"""按计划 Task 12 的规则筛选并排对比的候选案例，输出 side_by_side_candidates.json。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import valid_citation_ids
from cooling_rag_mg.numeric_norm import extract_numbers
from cooling_rag_mg.review_routing import _unit_of, derivation_type

E4 = ROOT / "data/search_results/exp_v4"
KB = {json.loads(l)["id"]: json.loads(l) for l in
      (ROOT / "data/processed/evidence_units_v3_audited.jsonl").open(encoding="utf-8")}


def main() -> None:
    rag = {r["source_requirement_id"]: r for r in json.loads((E4 / "rag_v4_results.json").read_text(encoding="utf-8"))["result_sets"]}
    nor = {r["source_requirement_id"]: r for r in json.loads((E4 / "norag_v4_results.json").read_text(encoding="utf-8"))["result_sets"]}
    case1, case2 = [], []
    for sid in sorted(rag):
        for a in rag[sid]["engineering_requirements"]:
            ua, na = _unit_of(str(a.get("measurable_criterion"))), extract_numbers(str(a.get("measurable_criterion")))
            ids = valid_citation_ids(a.get("evidence_citations", []), KB)
            for b in nor.get(sid, {}).get("engineering_requirements", []):
                if b.get("_grade") != "X":
                    continue
                ub, nb = _unit_of(str(b.get("measurable_criterion"))), extract_numbers(str(b.get("measurable_criterion")))
                if derivation_type(a, KB) == "Direct" and ua and ua == ub and na and nb \
                        and any(KB[i]["kb_tier"] == "L1" for i in ids) \
                        and abs(float(na[0]) - float(nb[0])) <= 0.2 * max(abs(float(na[0])), 1e-9):
                    case1.append({"or": sid, "rag": a, "norag": b, "cited": ids})
                if a.get("_grade") == "C" and "{{TBD" in str(a.get("measurable_criterion")) and ua and ua == ub:
                    case2.append({"or": sid, "rag": a, "norag": b, "cited": ids})
    pc = json.loads((E4 / "paired_conflict_analysis.json").read_text(encoding="utf-8"))
    out = {"case1_candidates": case1[:10], "case2_deferred_candidates": case2[:10], "paired_conflicts": pc}
    (E4 / "side_by_side_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("case1:", len(case1), "case2(deferred):", len(case2))


if __name__ == "__main__":
    main()
