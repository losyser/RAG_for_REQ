# scripts/71_paired_conflict_analysis.py
"""
配对冲突率分析：在两臂都生成了含数值 shall 的源需求子集（n=23）上，
用 Wilcoxon signed-rank 检验比较 RAG v3 与 no-RAG 的每源需求冲突率。

输入：data/search_results/exp_v3/norag_kb_verification.json
输出：data/search_results/exp_v3/paired_conflict_analysis.json
      data/search_results/exp_v3/paired_conflict_summary.txt
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VER_PATH = PROJECT_ROOT / "data" / "search_results" / "exp_v3" / "norag_kb_verification.json"
OUT_JSON  = PROJECT_ROOT / "data" / "search_results" / "exp_v3" / "paired_conflict_analysis.json"
OUT_TXT   = PROJECT_ROOT / "data" / "search_results" / "exp_v3" / "paired_conflict_summary.txt"


def main() -> None:
    with open(VER_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # Fix 1: guard against missing/empty "details"
    details = data.get("details")
    if not details:
        raise SystemExit(f"输入文件缺少 'details' 字段或为空: {VER_PATH}")

    # 按 arm × source_req 聚合，只保留有实质 label 的记录
    by_arm_req: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for row in details:
        if row.get("label") in ("conflict", "supported", "unverifiable"):
            by_arm_req[row["arm"]][row["sid"]].append(row["label"])

    rag_reqs   = set(by_arm_req["rag_v3"].keys())
    norag_reqs = set(by_arm_req["no_rag"].keys())
    paired_reqs = sorted(rag_reqs & norag_reqs)
    print(f"配对源需求（两臂均有数值shall）: {len(paired_reqs)}")

    # Fix 2: guard against too few paired requirements for Wilcoxon
    if len(paired_reqs) < 2:
        raise SystemExit(f"配对需求不足（{len(paired_reqs)}条），无法执行 Wilcoxon 检验")

    # 计算每个源需求的冲突率
    rows = []
    rag_rates, norag_rates = [], []
    for rid in paired_reqs:
        rag_labels   = by_arm_req["rag_v3"][rid]
        norag_labels = by_arm_req["no_rag"][rid]
        # Fix 3: guard against division by zero
        assert len(rag_labels) > 0 and len(norag_labels) > 0
        rag_conflict   = rag_labels.count("conflict")   / len(rag_labels)
        norag_conflict = norag_labels.count("conflict") / len(norag_labels)
        rag_rates.append(rag_conflict)
        norag_rates.append(norag_conflict)
        rows.append({
            "requirement_id": rid,
            "rag_n_shalls": len(rag_labels),
            "rag_conflict_rate": round(rag_conflict, 4),
            "norag_n_shalls": len(norag_labels),
            "norag_conflict_rate": round(norag_conflict, 4),
            "delta": round(norag_conflict - rag_conflict, 4),
        })

    # Fix 4: pre-compute means before building result dict
    rag_mean   = round(sum(rag_rates)   / len(rag_rates),   4)
    norag_mean = round(sum(norag_rates) / len(norag_rates), 4)

    # Wilcoxon signed-rank（双尾）
    stat, p = stats.wilcoxon(rag_rates, norag_rates, alternative="two-sided",
                             zero_method="pratt")

    result = {
        "n_paired": len(paired_reqs),
        "rag_mean_conflict_rate":   rag_mean,
        "norag_mean_conflict_rate": norag_mean,
        "wilcoxon_statistic": float(stat),
        "p_value": float(p),
        "significant_alpha_0_05": bool(p < 0.05),
        "per_requirement": rows,
    }

    # Fix 5: ensure output directory exists
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    summary_lines = [
        "=" * 55,
        "配对冲突率分析（post-hoc KB核查，paired Wilcoxon）",
        "=" * 55,
        f"配对源需求数: {result['n_paired']}",
        f"RAG v3 平均冲突率: {result['rag_mean_conflict_rate']:.4f}",
        f"no-RAG 平均冲突率: {result['norag_mean_conflict_rate']:.4f}",
        f"Wilcoxon W={result['wilcoxon_statistic']:.1f}, p={result['p_value']:.4f}",
        f"显著 (α=0.05): {result['significant_alpha_0_05']}",
    ]
    OUT_TXT.write_text("\n".join(summary_lines), encoding="utf-8")
    for line in summary_lines:
        print(line)
    print(f"\n结果写入: {OUT_JSON}")


if __name__ == "__main__":
    main()
