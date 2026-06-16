"""
Grade C shall 构成分析：
  - TBD with evidence  : KB有相关证据但没有精确数值 → 系统保守标记TBD（正确行为）
  - TBD without evidence: 既没数值也没证据
  - Qualitative        : 本质定性需求，无数值标准

输出 data/search_results/exp_v4/grade_c_analysis.json
     data/search_results/exp_v4/grade_c_analysis.csv
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RAG_FILE = ROOT / "data/search_results/exp_v4/rag_v4_results.json"
OR_JSONL  = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT_DIR   = ROOT / "data/search_results/exp_v4"

_TBD = re.compile(r"\{\{TBD\|")
_NUM = re.compile(
    r"\d+\.?\d*\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b)"
)


def load_or_map() -> dict[str, str]:
    m: dict[str, str] = {}
    with open(OR_JSONL, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            m[r["requirement_id"]] = r.get("requirement_text", "")
    return m


def categorize(mc: str, citations: list) -> str:
    if _TBD.search(mc):
        return "TBD_with_evidence" if citations else "TBD_no_evidence"
    return "qualitative"


def main():
    with open(RAG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    or_map = load_or_map()

    rows: list[dict] = []
    counts: dict[str, int] = {}

    for rs in data["result_sets"]:
        or_id = rs.get("source_requirement_id", "")
        or_text = or_map.get(or_id, "")
        for er in rs.get("engineering_requirements", []):
            if er.get("_grade") != "C":
                continue
            mc    = er.get("measurable_criterion", "")
            cits  = er.get("evidence_citations", [])
            cat   = categorize(mc, cits)
            counts[cat] = counts.get(cat, 0) + 1

            rows.append({
                "or_id":      or_id,
                "or_text":    or_text[:80],
                "shall":      er.get("shall_statement", "")[:100],
                "criterion":  mc[:120],
                "category":   cat,
                "n_citations": len(cits),
                "tiers":      "|".join(c.get("tier","") for c in cits),
            })

    total_c = len(rows)
    total   = sum(
        len(rs["engineering_requirements"])
        for rs in data["result_sets"]
    )

    summary = {
        "total_shalls": total,
        "total_grade_c": total_c,
        "grade_c_pct": round(total_c / total * 100, 1),
        "breakdown": {
            cat: {
                "count": n,
                "pct_of_c": round(n / total_c * 100, 1),
                "pct_of_all": round(n / total * 100, 1),
            }
            for cat, n in counts.items()
        },
        "interpretation": {
            "TBD_with_evidence": (
                "系统找到了相关证据但KB中无精确数值，保守标记TBD（诚实行为，非幻觉）"
            ),
            "TBD_no_evidence":   (
                "无证据支撑，TBD占位（需扩充KB）"
            ),
            "qualitative":       (
                "需求本质定性，不需要数值标准（正常现象）"
            ),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUT_DIR / "grade_c_analysis.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    fieldnames = ["or_id","or_text","shall","criterion","category","n_citations","tiers"]
    with open(OUT_DIR / "grade_c_analysis.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Total shalls: {total}")
    print(f"Grade C total: {total_c} ({total_c/total*100:.1f}%)")
    print()
    for cat, n in counts.items():
        print(f"  {cat}: {n} ({n/total_c*100:.1f}% of C, {n/total*100:.1f}% of all)")
    print()
    print(f"Saved: {OUT_DIR}/grade_c_analysis.json")
    print(f"Saved: {OUT_DIR}/grade_c_analysis.csv")


if __name__ == "__main__":
    main()
