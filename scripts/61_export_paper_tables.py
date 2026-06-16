# scripts/61_export_paper_tables.py
"""
从 eval_v3.json + expert_agreement.json 生成论文用 LaTeX 表格。

输出：
  data/paper_tables/table_descriptive.tex     — 描述统计表
  data/paper_tables/table_hhard.tex           — H_hard 矛盾率表
  data/paper_tables/table_blind_eval.tex      — 4维盲评汇总表
  data/paper_tables/table_expert_review.tex   — 专家评审汇总表
  data/paper_tables/table_combined_results.tex — 综合结果总表

用法：
  python scripts/61_export_paper_tables.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXP  = PROJECT_ROOT / "data" / "search_results" / "exp_v3"
DATA = PROJECT_ROOT / "data" / "processed"
OUT  = PROJECT_ROOT / "data" / "paper_tables"
COMPLIANCE_REPORT = PROJECT_ROOT / "data" / "search_results" / "compliance_metrics.json"
OUT.mkdir(exist_ok=True)

BLIND_DIMS = ["completeness", "actionability", "consistency", "verifiability"]
EXPERT_DIMS = ["decomposition", "accuracy", "completeness", "actionability", "overall"]


def _load_eval() -> dict:
    path = EXP / "eval_v3.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_expert() -> dict:
    path = DATA / "expert_agreement.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_compliance() -> dict:
    if not COMPLIANCE_REPORT.exists():
        return {}
    with open(COMPLIANCE_REPORT, encoding="utf-8") as f:
        return json.load(f)


# ── 1. 描述统计表 ──────────────────────────────────────────────────────────────

def table_descriptive(eval_data: dict) -> str:
    desc = eval_data.get("descriptive", {})
    rag = desc.get("rag_v3", {})
    norag = desc.get("no_rag", {})

    def fmt(d: dict, key: str, pct: bool = False) -> str:
        v = d.get(key)
        if v is None:
            return "---"
        return f"{v:.1\\%}" if pct else str(v)

    lines = [
        r"\begin{table}[H]",
        r"\caption{Descriptive statistics for RAG v3 and no-RAG outputs across 60 source requirements.}",
        r"\label{tab:descriptive}",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        r"\textbf{Metric} & \textbf{RAG v3} & \textbf{no-RAG (DeepSeek)} \\",
        r"\midrule",
        f"Total source requirements & {rag.get('n_sources','---')} & {norag.get('n_sources','---')} \\\\",
        f"Total engineering requirements & {rag.get('n_shalls','---')} & {norag.get('n_shalls','---')} \\\\",
        f"Numeric content ratio & {_pct(rag.get('numeric_fraction'))} & {_pct(norag.get('numeric_fraction'))} \\\\",
        f"Evidence attribution rate & {_pct(rag.get('attribution_rate'))} & {_pct(norag.get('attribution_rate'))} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ── 2. H_hard 矛盾率表 ─────────────────────────────────────────────────────────

def table_hhard(eval_data: dict) -> str:
    hh = eval_data.get("h_hard", {})
    rag_stats = hh.get("rag_v3", {})
    norag_stats = hh.get("no_rag", {})
    wx = hh.get("wilcoxon", {})

    rag_vals = [s["h_hard"] for s in rag_stats.values() if s.get("h_hard") is not None]
    norag_vals = [s["h_hard"] for s in norag_stats.values() if s.get("h_hard") is not None]

    def mean_std(vals):
        if not vals:
            return "---", "---"
        n = len(vals)
        m = sum(vals) / n
        var = sum((x - m) ** 2 for x in vals) / n
        return f"{m:.4f}", f"{math.sqrt(var):.4f}"

    rm, rs = mean_std(rag_vals)
    nm, ns = mean_std(norag_vals)
    p = wx.get("p_value")
    p_str = f"{p:.4f}" if p is not None and not (isinstance(p, float) and math.isnan(p)) else "---"
    n_pairs = wx.get("n_pairs", "---")

    lines = [
        r"\begin{table}[H]",
        r"\caption{H$_\mathrm{hard}$ contradiction rate per source requirement. Lower is better. "
        r"Paired Wilcoxon signed-rank test.}",
        r"\label{tab:hhard}",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"\textbf{System} & \textbf{Mean} & \textbf{Std} & \textbf{Wilcoxon $p$} \\",
        r"\midrule",
        f"RAG v3  & {rm} & {rs} & \\multirow{{2}}{{*}}{{{p_str} ($n$={n_pairs})}} \\\\",
        f"no-RAG  & {nm} & {ns} & \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ── 3. 4维盲评表 ───────────────────────────────────────────────────────────────

def table_blind_eval(eval_data: dict) -> str:
    agg = eval_data.get("blind_quality", {}).get("aggregate", {})
    n_total = len(eval_data.get("blind_quality", {}).get("per_source", []))

    lines = [
        r"\begin{table}[H]",
        r"\caption{Blind pairwise quality evaluation results (RAG v3 vs. no-RAG, $N=" + str(n_total) + r"$ source requirements). "
        r"Left--right swap applied to remove position bias. R = RAG v3 wins, tie = no preference, B0 = no-RAG wins.}",
        r"\label{tab:blind_eval}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"\textbf{Dimension} & \textbf{R (RAG v3)} & \textbf{Tie} & \textbf{B0 (no-RAG)} & \textbf{Win rate (R)} \\",
        r"\midrule",
    ]

    for dim in BLIND_DIMS:
        d = agg.get(dim, {})
        r = d.get("R", 0)
        t = d.get("tie", 0)
        b = d.get("B0", 0)
        rate = _win_rate(r, r + t + b)
        lines.append(f"{dim.capitalize()} & {r} & {t} & {b} & {rate} \\\\")

    ov = agg.get("overall", {})
    r = ov.get("R", 0); t = ov.get("tie", 0); b = ov.get("B0", 0)
    rate = _win_rate(r, r + t + b)
    lines += [
        r"\midrule",
        f"\\textbf{{Overall}} & {r} & {t} & {b} & {rate} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ── 4. 专家评审表 ──────────────────────────────────────────────────────────────

def table_expert_review(expert_data: dict) -> str:
    agg = expert_data.get("aggregate", {})
    n = expert_data.get("n_reviewed", 0)
    kappa = expert_data.get("kappa_overall")
    kappa_str = f"{kappa:.3f}" if kappa is not None else "---"

    lines = [
        r"\begin{table}[H]",
        r"\caption{Expert holistic review results ($N=" + str(n) + r"$ sampled requirements, "
        f"two independent reviewers, Cohen's $\\kappa={kappa_str}$). "
        r"Disagreement resolved to tie.}",
        r"\label{tab:expert_review}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"\textbf{Dimension} & \textbf{RAG v3 wins} & \textbf{Tie} & \textbf{no-RAG wins} & \textbf{RAG v3 rate} \\",
        r"\midrule",
    ]

    for dim in EXPERT_DIMS:
        d = agg.get(dim, {})
        rv = d.get("rag_v3", 0)
        t  = d.get("tie", 0)
        nv = d.get("no_rag", 0)
        nn = d.get("n", 0)
        rate = _win_rate(rv, nn)
        kd = d.get("kappa")
        kd_str = f"{kd:.2f}" if kd is not None else "---"
        lines.append(
            f"{dim.capitalize()} & {rv} & {t} & {nv} & {rate} ($\\kappa$={kd_str}) \\\\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ── 5. 合规指标表 ──────────────────────────────────────────────────────────────

def table_compliance(compliance_data: dict) -> str:
    summary = compliance_data.get("summary", {})
    rag = summary.get("RAG_v3", {})
    norag = summary.get("no_RAG", {})
    detail = compliance_data.get("detail", {})
    rag_detail = detail.get("RAG_v3", {})

    total_l1 = rag_detail.get("total_l1_units", "---")
    covered_l1 = rag_detail.get("covered_l1_units", "---")
    n_shalls_rag = rag_detail.get("n_shalls", "---")

    def fmt(v) -> str:
        if v is None:
            return "---"
        return f"{v * 100:.1f}\\%"

    lines = [
        r"\begin{table}[H]",
        r"\caption{Regulatory compliance traceability metrics for RAG v3 vs.\ no-RAG "
        r"(60 source requirements; no-RAG has no evidence references by design, "
        r"so all three metrics are 0\% by construction). "
        r"RCR\,=\,Regulatory Coverage Rate; CC\,=\,Compliance Completeness; "
        r"RR\,=\,Review Readiness. "
        r"L1 units: KB entries tagged as regulatory-tier "
        r"(ship\_rule / class\_rule; $N_{\mathrm{L1}}=" + str(total_l1) + r"$).}",
        r"\label{tab:compliance}",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"\textbf{Metric} & \textbf{Definition} & \textbf{RAG v3} & \textbf{no-RAG} \\",
        r"\midrule",
        f"RCR & Shalls with $\\geq$1 L1 citation & {fmt(rag.get('RCR'))} & {fmt(norag.get('RCR'))} \\\\",
        f"CC  & L1 units cited $\\div$ total L1 units ({total_l1}) & {fmt(rag.get('CC'))} & {fmt(norag.get('CC'))} \\\\",
        f"RR  & Shalls with $\\geq$1 direct L1 citation & {fmt(rag.get('RR'))} & {fmt(norag.get('RR'))} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ── helpers ────────────────────────────────────────────────────────────────────

def _pct(v) -> str:
    if v is None:
        return "---"
    return "{:.1f}\\%".format(v * 100)


def _win_rate(num: int, total: int) -> str:
    if total == 0:
        return "---"
    return "{:.1f}\\%".format(100.0 * num / total)


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    eval_data        = _load_eval()
    expert_data      = _load_expert()
    compliance_data  = _load_compliance()

    tables = {
        "table_descriptive.tex":      table_descriptive(eval_data),
        "table_hhard.tex":            table_hhard(eval_data),
        "table_blind_eval.tex":       table_blind_eval(eval_data),
        "table_expert_review.tex":    table_expert_review(expert_data),
        "table_compliance.tex":       table_compliance(compliance_data),
    }

    for fname, content in tables.items():
        p = OUT / fname
        p.write_text(content, encoding="utf-8")
        print(f"写入: {p}")

    # 综合摘要
    summary_lines = [
        "% ================================================================",
        "% 论文数据汇总 (auto-generated by scripts/61_export_paper_tables.py)",
        "% ================================================================",
        "",
    ]
    hh = eval_data.get("h_hard", {})
    wx = hh.get("wilcoxon", {})
    summary_lines += [
        f"% H_hard: RAG v3 mean={wx.get('rag_mean','N/A'):.4f}, no-RAG mean={wx.get('norag_mean','N/A'):.4f}, p={wx.get('p_value','N/A')}"
        if wx else "% H_hard: not available",
    ]
    blind_agg = eval_data.get("blind_quality", {}).get("aggregate", {})
    for dim in BLIND_DIMS:
        d = blind_agg.get(dim, {})
        summary_lines.append(
            f"% Blind {dim}: R={d.get('R',0)} tie={d.get('tie',0)} B0={d.get('B0',0)}"
        )
    if expert_data:
        summary_lines.append(
            f"% Expert kappa={expert_data.get('kappa_overall','N/A')}, n={expert_data.get('n_reviewed',0)}"
        )
    if compliance_data:
        s = compliance_data.get("summary", {})
        rag_c = s.get("RAG_v3", {})
        summary_lines.append(
            f"% Compliance RAG: RCR={rag_c.get('RCR','N/A'):.3f}, "
            f"CC={rag_c.get('CC','N/A'):.3f}, RR={rag_c.get('RR','N/A'):.3f} | no-RAG: 0/0/0"
        )

    (OUT / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"写入: {OUT / 'summary.txt'}")


if __name__ == "__main__":
    main()
