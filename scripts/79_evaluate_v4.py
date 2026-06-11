"""
v4 实验评估：Grade A/B/C/X 分布 + 引用率 + L1率 + 多来源率。
输入：exp_v4/rag_v4_results.json + norag_v4_results.json
输出：exp_v4/eval_v4_summary.json + exp_v4/eval_v4_grades.csv
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXP_DIR  = ROOT / "data/search_results/exp_v4"
RAG_FILE = EXP_DIR / "rag_v4_results.json"
NOR_FILE = EXP_DIR / "norag_v4_results.json"
OUT_JSON = EXP_DIR / "eval_v4_summary.json"
OUT_CSV  = EXP_DIR / "eval_v4_grades.csv"


def collect_shalls(results: dict) -> list[dict]:
    shalls = []
    for rs in results.get("result_sets", []):
        or_id = rs["source_requirement_id"]
        for er in rs.get("engineering_requirements", []):
            er_copy = dict(er)
            er_copy["_or_id"] = or_id
            shalls.append(er_copy)
    return shalls


def compute_metrics(shalls: list[dict], arm: str) -> dict:
    n = len(shalls)
    if n == 0:
        return {"arm": arm, "n_shalls": 0}

    grade_counts = Counter(er.get("_grade", "?") for er in shalls)
    cited = sum(1 for er in shalls if er.get("evidence_citations"))
    has_l1 = sum(
        1 for er in shalls
        if any(c.get("tier") == "L1" for c in er.get("evidence_citations", []))
    )
    multi_src = sum(
        1 for er in shalls if len(er.get("evidence_citations", [])) >= 2
    )

    return {
        "arm": arm,
        "n_shalls": n,
        "grade_A": grade_counts.get("A", 0),
        "grade_B": grade_counts.get("B", 0),
        "grade_C": grade_counts.get("C", 0),
        "grade_X": grade_counts.get("X", 0),
        "grade_A_pct": round(grade_counts.get("A", 0) / n * 100, 1),
        "grade_B_pct": round(grade_counts.get("B", 0) / n * 100, 1),
        "grade_C_pct": round(grade_counts.get("C", 0) / n * 100, 1),
        "grade_X_pct": round(grade_counts.get("X", 0) / n * 100, 1),
        "citation_rate_pct": round(cited / n * 100, 1),
        "l1_citation_rate_pct": round(has_l1 / n * 100, 1),
        "multi_source_rate_pct": round(multi_src / n * 100, 1),
    }


def print_summary(m: dict):
    arm = m["arm"]
    n = m["n_shalls"]
    print(f"\n{'='*50}")
    print(f"  {arm}  (n={n})")
    print(f"{'='*50}")
    print(f"  Grade A (精确有据):  {m.get('grade_A',0):4d}  ({m.get('grade_A_pct',0):5.1f}%)")
    print(f"  Grade B (范围有据):  {m.get('grade_B',0):4d}  ({m.get('grade_B_pct',0):5.1f}%)")
    print(f"  Grade C (安全占位):  {m.get('grade_C',0):4d}  ({m.get('grade_C_pct',0):5.1f}%)")
    print(f"  Grade X (危险数值):  {m.get('grade_X',0):4d}  ({m.get('grade_X_pct',0):5.1f}%)")
    print(f"  ---")
    print(f"  KB引用率:            {m.get('citation_rate_pct',0):5.1f}%")
    print(f"  L1引用率:            {m.get('l1_citation_rate_pct',0):5.1f}%")
    print(f"  多来源率(≥2):        {m.get('multi_source_rate_pct',0):5.1f}%")


def main():
    if not RAG_FILE.exists():
        print(f"ERROR: {RAG_FILE} not found. Run script 77 first.")
        sys.exit(1)
    if not NOR_FILE.exists():
        print(f"ERROR: {NOR_FILE} not found. Run script 78 first.")
        sys.exit(1)

    with open(RAG_FILE, encoding="utf-8") as f:
        rag = json.load(f)
    with open(NOR_FILE, encoding="utf-8") as f:
        nor = json.load(f)

    rag_shalls = collect_shalls(rag)
    nor_shalls = collect_shalls(nor)

    rag_metrics = compute_metrics(rag_shalls, "rag-v4")
    nor_metrics = compute_metrics(nor_shalls, "norag-v4")

    print_summary(rag_metrics)
    print_summary(nor_metrics)

    summary = {"rag": rag_metrics, "norag": nor_metrics}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSaved summary → {OUT_JSON}")

    rows = []
    for er in rag_shalls:
        rows.append({
            "arm": "rag-v4",
            "or_id": er.get("_or_id", ""),
            "grade": er.get("_grade", "?"),
            "measurable_criterion": er.get("measurable_criterion", ""),
            "n_citations": len(er.get("evidence_citations", [])),
            "shall_statement": er.get("shall_statement", "")[:100],
        })
    for er in nor_shalls:
        rows.append({
            "arm": "norag-v4",
            "or_id": er.get("_or_id", ""),
            "grade": er.get("_grade", "?"),
            "measurable_criterion": er.get("measurable_criterion", ""),
            "n_citations": 0,
            "shall_statement": er.get("shall_statement", "")[:100],
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["arm", "or_id", "grade", "measurable_criterion", "n_citations", "shall_statement"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved per-shall CSV → {OUT_CSV}")


if __name__ == "__main__":
    main()
