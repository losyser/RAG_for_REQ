# -*- coding: utf-8 -*-
"""
Script 23: Export M1–M5 metrics as LaTeX table for the paper.

Usage:
    python scripts/23_export_latex_table.py --exp-dir <path/to/experiment/>
    python scripts/23_export_latex_table.py  # auto-finds latest batch
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config

# ─────────────────────────────────────────────
# 展示名称与分组
# ─────────────────────────────────────────────

_GROUP_LABELS = {
    "G1": r"\textbf{G1} Direct LLM",
    "G2": r"\textbf{G2} Flat RAG",
    "G3": r"\textbf{G3} Multi-RAG",
    "G4": r"\textbf{G4} Proposed",
    "A1": r"\textit{A1} w/o QualityGate",
    "A2": r"\textit{A2} w/o ProfileScore",
}

_METRIC_HEADERS = [
    r"M1$\downarrow$",
    r"M2$\uparrow$",
    r"M3$\downarrow$",
    r"M4$\uparrow$",
    r"M5$\uparrow$",
]


def _pct(v: float) -> str:
    if v != v:  # nan
        return r"\multicolumn{1}{c}{---}"
    return f"{v * 100:.1f}\\%"


def _best_in_column(rows: list[dict], metric: str, higher_better: bool) -> float | None:
    vals = [r[metric] for r in rows if r[metric] == r[metric]]
    if not vals:
        return None
    return max(vals) if higher_better else min(vals)


def generate_latex_table(rows: list[dict]) -> str:
    higher_better = {
        "m1": False, "m2": True, "m3": False, "m4": True, "m5": True
    }
    bests = {m: _best_in_column(rows, m, hb) for m, hb in higher_better.items()}

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Comparison of M1--M5 metrics across experiment groups. "
        r"Best values per metric are \textbf{bold}. "
        r"$\downarrow$: lower is better; $\uparrow$: higher is better.}",
        r"\label{tab:metrics}",
        r"\setlength{\tabcolsep}{5pt}",
        r"\begin{tabular}{l r r " + "r " * 5 + r"}",
        r"\toprule",
        r"Group & $N_\text{sets}$ & $N_\text{reqs}$ & "
        + " & ".join(_METRIC_HEADERS) + r" \\",
        r"\midrule",
    ]

    # Separator before ablation groups
    ablation_started = False

    for row in rows:
        group = row["group"]
        if group in ("A1", "A2") and not ablation_started:
            lines.append(r"\midrule")
            ablation_started = True

        label = _GROUP_LABELS.get(group, group)
        cells = []
        for m in ["m1", "m2", "m3", "m4", "m5"]:
            val = row[m]
            cell = _pct(val)
            # Bold the best value (skip nan)
            if val == val and bests[m] is not None and abs(val - bests[m]) < 1e-9:
                # Wrap in \textbf but keep the % sign outside if it's a \multicolumn
                cell = r"\textbf{" + f"{val * 100:.1f}" + r"\%}"
            cells.append(cell)

        lines.append(
            f"{label} & {row['n_sets']} & {row['n_reqs']} & "
            + " & ".join(cells) + r" \\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


def generate_markdown_table(rows: list[dict]) -> str:
    header = "| Group | N_sets | N_reqs | M1 EFR↓ | M2 QGP↑ | M3 OIR↓ | M4 VER↑ | M5 MBSE↑ |"
    sep = "|---|---|---|---|---|---|---|---|"
    data_lines = []
    for row in rows:
        def f(v: float) -> str:
            return "N/A" if v != v else f"{v * 100:.1f}%"
        data_lines.append(
            f"| {row['group']} | {row['n_sets']} | {row['n_reqs']} | "
            f"{f(row['m1'])} | {f(row['m2'])} | {f(row['m3'])} | "
            f"{f(row['m4'])} | {f(row['m5'])} |"
        )
    return "\n".join([header, sep] + data_lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", default=None)
    args = parser.parse_args()

    cfg = get_config()

    if args.exp_dir:
        exp_dir = Path(args.exp_dir)
    else:
        batches = sorted(cfg.paths.search_results_dir.glob("batch_*/experiment"))
        if not batches:
            print("No experiment directory found. Run scripts 21 and 22 first.")
            sys.exit(1)
        exp_dir = batches[-1]

    metrics_path = exp_dir / "metrics_summary.json"
    if not metrics_path.exists():
        print(f"metrics_summary.json not found in {exp_dir}")
        print("Run: python scripts/22_compute_metrics.py")
        sys.exit(1)

    rows: list[dict] = json.loads(metrics_path.read_text(encoding="utf-8"))
    print(f"Loaded metrics for {len(rows)} group(s) from {metrics_path}\n")

    latex = generate_latex_table(rows)
    md = generate_markdown_table(rows)

    latex_path = exp_dir / "table_metrics.tex"
    md_path = exp_dir / "table_metrics.md"

    latex_path.write_text(latex, encoding="utf-8")
    md_path.write_text(md, encoding="utf-8")

    print("=== Markdown preview ===")
    print(md)
    print(f"\nLaTeX table → {latex_path}")
    print(f"Markdown    → {md_path}")


if __name__ == "__main__":
    main()
