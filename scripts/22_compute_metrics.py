# -*- coding: utf-8 -*-
"""
Script 22: Compute M1–M5 metrics from experiment results, print comparison table.

Metrics (all auto-computed):
  M1  Evidence-free generation rate   — evidence_ids empty / total
  M2  Quality gate pass rate          — overall_passed=True / total  (G4/A2 only)
  M3  Over-inference rate             — over_inference failed / total (all groups)
  M4  Verifiability score             — verifiability passed / total  (all groups)
  M5  MBSE completeness rate          — mbse_completeness passed / total (all groups)

M6 (traceability precision) requires manual review — a sampling template is printed.

Usage:
    python scripts/22_compute_metrics.py --exp-dir <path/to/experiment/>
    python scripts/22_compute_metrics.py  # auto-finds latest batch
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.text_utils import safe_text


# ─────────────────────────────────────────────
# 加载与指标计算
# ─────────────────────────────────────────────

def _load_group(exp_dir: Path, group: str) -> list[dict[str, Any]]:
    candidates = list(exp_dir.glob(f"{group}_*.jsonl"))
    if not candidates:
        return []
    return read_jsonl(str(candidates[0]))


def _flatten_requirements(result_sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten all engineering_requirements from all result sets."""
    out = []
    for rs in result_sets:
        for er in (rs.get("engineering_requirements") or []):
            er = dict(er)
            er["_group"] = rs.get("_group", "")
            er["_set_id"] = rs.get("requirement_set_id", "")
            out.append(er)
    return out


def _m1_evidence_free_rate(reqs: list[dict[str, Any]]) -> float:
    if not reqs:
        return float("nan")
    empty = sum(1 for r in reqs if not (r.get("evidence_ids") or []))
    return round(empty / len(reqs), 4)


def _m2_qg_pass_rate(reqs: list[dict[str, Any]]) -> float:
    """Only meaningful for groups with quality_gate_report attached."""
    has_report = [r for r in reqs if r.get("quality_gate_report")]
    if not has_report:
        return float("nan")
    passed = sum(1 for r in has_report
                 if (r.get("quality_gate_report") or {}).get("overall_passed"))
    return round(passed / len(has_report), 4)


def _m3_over_inference_rate(reqs: list[dict[str, Any]], qg: QualityGate) -> float:
    """Run over_inference check on every requirement (fast, rule-based)."""
    if not reqs:
        return float("nan")
    failed = sum(
        1 for r in reqs
        if not qg._over_inference(r).passed  # noqa: SLF001
    )
    return round(failed / len(reqs), 4)


def _m4_verifiability_score(reqs: list[dict[str, Any]], qg: QualityGate) -> float:
    """Fraction of requirements passing the verifiability check (rule-based)."""
    if not reqs:
        return float("nan")
    passed = sum(1 for r in reqs if qg._verifiability(r).passed)  # noqa: SLF001
    return round(passed / len(reqs), 4)


def _m5_mbse_completeness(reqs: list[dict[str, Any]], qg: QualityGate) -> float:
    if not reqs:
        return float("nan")
    passed = sum(1 for r in reqs if qg._mbse_completeness(r).passed)  # noqa: SLF001
    return round(passed / len(reqs), 4)


# ─────────────────────────────────────────────
# 报告输出
# ─────────────────────────────────────────────

def _fmt(v: float) -> str:
    if v != v:  # nan
        return "  N/A "
    return f"{v * 100:5.1f}%"


def _print_table(rows: list[dict[str, Any]]) -> None:
    header = f"{'Group':<6} {'N_sets':>7} {'N_reqs':>7} "
    header += f"{'M1 EFR':>8} {'M2 QGP':>8} {'M3 OIR':>8} {'M4 VER':>8} {'M5 MBSE':>8}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    for row in rows:
        line = (
            f"{row['group']:<6} "
            f"{row['n_sets']:>7} "
            f"{row['n_reqs']:>7} "
            f"{_fmt(row['m1']):>8} "
            f"{_fmt(row['m2']):>8} "
            f"{_fmt(row['m3']):>8} "
            f"{_fmt(row['m4']):>8} "
            f"{_fmt(row['m5']):>8}"
        )
        print(line)
    print("=" * len(header))
    print(
        "\nM1=Evidence-Free Rate (↓ better)  M2=QG Pass Rate (↑ better)\n"
        "M3=Over-Inference Rate (↓ better) M4=Verifiability Score (↑ better)\n"
        "M5=MBSE Completeness (↑ better)   N/A=metric not applicable for this group"
    )


def _print_m6_sampling(exp_dir: Path, group: str = "G4", n: int = 20) -> None:
    result_sets = _load_group(exp_dir, group)
    if not result_sets:
        return
    reqs = _flatten_requirements(result_sets)
    sample = reqs[:n]
    out = []
    for i, r in enumerate(sample, start=1):
        out.append({
            "index": i,
            "requirement_id": safe_text(r.get("id")),
            "shall_statement": safe_text(r.get("shall_statement"))[:200],
            "evidence_ids": r.get("evidence_ids") or [],
            "support_status": safe_text(r.get("support_status")),
            "M6_human_judgement": {
                "traceability_correct": None,   # True / False
                "notes": "",
            },
        })
    sampling_path = exp_dir / "M6_sampling_template.json"
    sampling_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nM6 sampling template ({n} items) saved → {sampling_path}")
    print("Fill in 'traceability_correct' manually, then compute precision as true_count / n.")


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", default=None,
                        help="Path to experiment/ subdirectory. Auto-detected if omitted.")
    args = parser.parse_args()

    cfg = get_config()

    if args.exp_dir:
        exp_dir = Path(args.exp_dir)
    else:
        batches = sorted(cfg.paths.search_results_dir.glob("batch_*/experiment"))
        if not batches:
            print("No experiment directory found. Run script 21 first.")
            sys.exit(1)
        exp_dir = batches[-1]

    print(f"Computing metrics from: {exp_dir}")
    qg = QualityGate()

    rows = []
    for group in ["G1", "G2", "G3", "G4", "A1", "A2"]:
        result_sets = _load_group(exp_dir, group)
        if not result_sets:
            continue
        reqs = _flatten_requirements(result_sets)
        rows.append({
            "group": group,
            "n_sets": len(result_sets),
            "n_reqs": len(reqs),
            "m1": _m1_evidence_free_rate(reqs),
            "m2": _m2_qg_pass_rate(reqs),
            "m3": _m3_over_inference_rate(reqs, qg),
            "m4": _m4_verifiability_score(reqs, qg),
            "m5": _m5_mbse_completeness(reqs, qg),
        })

    _print_table(rows)

    # Save as JSON for paper
    metrics_path = exp_dir / "metrics_summary.json"
    metrics_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nMetrics saved → {metrics_path}")

    # M6 sampling template
    _print_m6_sampling(exp_dir, group="G4", n=20)


if __name__ == "__main__":
    main()
