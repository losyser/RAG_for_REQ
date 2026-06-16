# scripts/60_expert_agreement.py
"""
专家评审一致性分析 + 汇总评分

输入：data/processed/expert_sample.json（expert1/expert2 字段已填写）

输出：
  data/processed/expert_agreement.json  — 完整结果
  data/processed/expert_agreement.txt   — 可读摘要

指标：
  - Cohen's Kappa（逐维度 + 总体）
  - 各维度 RAG v3 / 平局 / no-RAG 胜出次数（两位专家共识）
  - 两专家对比（分歧记录）
  - 最终汇总（取共识，分歧→tie）
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "processed"
SAMPLE_PATH = DATA / "expert_sample.json"

DIMS = ["decomposition", "accuracy", "completeness", "actionability", "overall"]
VALID = {"A", "tie", "B", ""}


def _canonical(val: str, system_a: str) -> str | None:
    """Convert A/B/tie to rag_v3/no_rag/tie; empty → None (not reviewed)."""
    v = val.strip()
    if not v:
        return None
    if v == "tie":
        return "tie"
    if v == "A":
        return system_a          # "rag_v3" or "no_rag"
    if v == "B":
        return "no_rag" if system_a == "rag_v3" else "rag_v3"
    return None


def cohen_kappa(labels_e1: list[str], labels_e2: list[str]) -> float | None:
    """Compute Cohen's Kappa for two raters over matching labels."""
    assert len(labels_e1) == len(labels_e2)
    n = len(labels_e1)
    if n == 0:
        return None
    all_cats = sorted(set(labels_e1) | set(labels_e2))
    # observed agreement
    p_o = sum(a == b for a, b in zip(labels_e1, labels_e2)) / n
    # expected agreement
    p_e = sum(
        (labels_e1.count(c) / n) * (labels_e2.count(c) / n)
        for c in all_cats
    )
    if p_e >= 1.0:
        return 1.0
    return (p_o - p_e) / (1.0 - p_e)


def main() -> None:
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        records = json.load(f)

    completed = [
        r for r in records
        if r.get("expert1", {}).get("overall") and r.get("expert2", {}).get("overall")
    ]
    print(f"已完成双人评审：{len(completed)} / {len(records)} 条")
    if not completed:
        print("尚无已完成的评审，请先运行 expert_review_ui.py")
        sys.exit(0)

    # ── 逐维度收集标签对 ──────────────────────────────────────────────────────
    # labels_e1/e2[dim] = list of "rag_v3"/"no_rag"/"tie"
    labels_e1: dict[str, list[str]] = defaultdict(list)
    labels_e2: dict[str, list[str]] = defaultdict(list)
    disagree_rows: list[dict] = []

    for r in completed:
        sa = r["system_a"]   # "rag_v3" or "no_rag"
        e1 = r.get("expert1", {})
        e2 = r.get("expert2", {})

        rid = r["requirement_id"]
        any_disagree = False
        for dim in DIMS:
            v1 = _canonical(e1.get(dim, ""), sa)
            v2 = _canonical(e2.get(dim, ""), sa)
            if v1 is None or v2 is None:
                continue
            labels_e1[dim].append(v1)
            labels_e2[dim].append(v2)
            if v1 != v2:
                any_disagree = True
        if any_disagree:
            disagree_rows.append({
                "requirement_id": rid,
                "expert1": {d: _canonical(e1.get(d, ""), sa) for d in DIMS},
                "expert2": {d: _canonical(e2.get(d, ""), sa) for d in DIMS},
            })

    # ── Cohen's Kappa ─────────────────────────────────────────────────────────
    kappa_per_dim: dict[str, float | None] = {}
    for dim in DIMS:
        kappa_per_dim[dim] = cohen_kappa(labels_e1[dim], labels_e2[dim])

    all_e1 = [v for dim in DIMS for v in labels_e1[dim]]
    all_e2 = [v for dim in DIMS for v in labels_e2[dim]]
    kappa_overall = cohen_kappa(all_e1, all_e2)

    # ── 共识汇总（分歧 → tie）─────────────────────────────────────────────────
    consensus: dict[str, list[str]] = defaultdict(list)  # dim → list of canonical labels
    for r in completed:
        sa = r["system_a"]
        e1 = r.get("expert1", {})
        e2 = r.get("expert2", {})
        final = {}
        for dim in DIMS:
            v1 = _canonical(e1.get(dim, ""), sa)
            v2 = _canonical(e2.get(dim, ""), sa)
            if v1 is None or v2 is None:
                c = v1 or v2 or "tie"
            elif v1 == v2:
                c = v1
            else:
                c = "tie"
            final[dim] = c
            consensus[dim].append(c)
        # write back to record
        r["final"] = {d: final[d] for d in DIMS}

    with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # ── 汇总统计 ──────────────────────────────────────────────────────────────
    agg: dict[str, dict] = {}
    for dim in DIMS:
        ctr = Counter(consensus[dim])
        n = len(consensus[dim])
        agg[dim] = {
            "rag_v3": ctr.get("rag_v3", 0),
            "tie":    ctr.get("tie", 0),
            "no_rag": ctr.get("no_rag", 0),
            "n":      n,
            "rag_v3_rate": ctr.get("rag_v3", 0) / n if n else 0,
            "no_rag_rate": ctr.get("no_rag", 0) / n if n else 0,
            "kappa": kappa_per_dim.get(dim),
        }

    result = {
        "n_reviewed": len(completed),
        "n_total": len(records),
        "kappa_per_dim": kappa_per_dim,
        "kappa_overall": kappa_overall,
        "aggregate": agg,
        "disagreements": disagree_rows,
    }

    out_json = DATA / "expert_agreement.json"
    out_txt  = DATA / "expert_agreement.txt"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    _write_summary(result, out_txt)
    print(f"\n结果写入: {out_json}")
    print(f"摘要写入: {out_txt}")


def _write_summary(result: dict, path: Path) -> None:
    lines = ["=" * 60, "专家评审一致性分析", "=" * 60, ""]
    lines.append(f"已完成评审：{result['n_reviewed']} / {result['n_total']} 条")
    lines.append(f"总体 Cohen's Kappa：{_fmt_kappa(result['kappa_overall'])}")
    lines.append("")

    lines.append("【逐维度结果（两专家共识）】")
    lines.append(f"  {'维度':<14s}  RAG v3  平局  no-RAG  Kappa   解释")
    lines.append("  " + "-" * 58)
    for dim in DIMS:
        d = result["aggregate"][dim]
        kappa = d["kappa"]
        interp = _kappa_interp(kappa)
        lines.append(
            f"  {dim:<14s}  {d['rag_v3']:>6d}  {d['tie']:>4d}  {d['no_rag']:>6d}  "
            f"{_fmt_kappa(kappa):>6s}  {interp}"
        )
    lines.append("")

    lines.append("【分歧条目】")
    for row in result["disagreements"]:
        lines.append(f"  {row['requirement_id']}")
        for dim in DIMS:
            v1 = row["expert1"].get(dim, "?")
            v2 = row["expert2"].get(dim, "?")
            if v1 != v2:
                lines.append(f"    {dim:<14s}: 专家1={v1}  专家2={v2}")
    if not result["disagreements"]:
        lines.append("  无分歧（完全一致）")

    path.write_text("\n".join(lines), encoding="utf-8")
    for l in lines:
        print(l)


def _fmt_kappa(k) -> str:
    if k is None:
        return "  N/A"
    return f"{k:+.3f}"


def _kappa_interp(k) -> str:
    if k is None:
        return "数据不足"
    if k < 0:
        return "低于随机"
    if k < 0.20:
        return "轻度一致"
    if k < 0.40:
        return "一般一致"
    if k < 0.60:
        return "中度一致"
    if k < 0.80:
        return "较强一致"
    return "近乎完美"


if __name__ == "__main__":
    main()
