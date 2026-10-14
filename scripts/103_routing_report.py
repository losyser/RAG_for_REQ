# scripts/103_routing_report.py
"""对 RAG 和 no-RAG 结果统计派生类型、冲突数、路由分布，并导出 30 条人工核验样本（SEED=42）。"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.review_routing import conflict_flag, derivation_type, review_route

E4 = ROOT / "data/search_results/exp_v4"
KB = {json.loads(l)["id"]: json.loads(l) for l in
      (ROOT / "data/processed/evidence_units_v3_audited.jsonl").open(encoding="utf-8")}


def main() -> None:
    rep, conflicts, sample_pool = {}, [], []
    for arm, fn in [("rag", "rag_v4_results.json"), ("norag", "norag_v4_results.json")]:
        d = json.loads((E4 / fn).read_text(encoding="utf-8"))
        dt, rt, why_c = Counter(), Counter(), Counter()
        for rs in d["result_sets"]:
            ev = rs.get("_evidence_values", {})
            for k, er in enumerate(rs["engineering_requirements"]):
                dt[derivation_type(er, KB)] += 1
                route, why = review_route(er, KB, ev)
                rt[route] += 1
                why_c[f"{route}: {why}"] += 1
                f = conflict_flag(er, KB, ev)
                if f:
                    conflicts.append({"or": rs["source_requirement_id"], "k": k, **f,
                                      "criterion": er.get("measurable_criterion")})
                if arm == "rag":
                    sample_pool.append((rs["source_requirement_id"], k, er))
        rep[arm] = {"derivation": dict(dt), "routes": dict(rt), "route_reasons": dict(why_c)}
    rep["conflicts"] = conflicts
    rep["n_conflicts"] = len(conflicts)
    (E4 / "routing_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    rng = random.Random(42)
    with (E4 / "derivation_validation_30.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["or", "k", "rule_type", "manual_type", "criterion", "cited_texts"])
        for sid, k, er in rng.sample(sample_pool, min(30, len(sample_pool))):
            from cooling_rag_mg.grade_classifier import valid_citation_ids
            ids = valid_citation_ids(er.get("evidence_citations", []), KB)
            w.writerow([sid, k, derivation_type(er, KB), "", er.get("measurable_criterion"),
                        " || ".join(f"{i}: {KB[i]['text'][:300]}" for i in ids)])
    print(json.dumps({k: v for k, v in rep.items() if k != "conflicts"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
