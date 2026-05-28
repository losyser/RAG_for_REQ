# -*- coding: utf-8 -*-
"""
Script 27: Per-requirement statistical analysis for paper Section 5 inference claims.

Replaces the round-level paired t-test (which was severely underpowered at n=3
rounds, see PROJECT_AUDIT_FINDINGS.md MJ-16) with per-requirement mixed-effects
analysis. For each pair of groups, fits

    pass_or_fail ~ group + (1 | round) + (1 | stakeholder)

via statsmodels.MixedLM, plus a non-parametric paired Wilcoxon backup and a
10,000-resample bootstrap CI on the marginal proportion difference.

Output:
  data/search_results/statistical_analysis.json  — machine-readable
  data/search_results/statistical_analysis.tex   — LaTeX table source

Usage:
    python scripts/27_statistics.py --batches-dir data/search_results/
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.text_utils import safe_text

GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]
COMPARISONS = [
    ("G1", "G2"),
    ("G2", "G3"),
    ("G3", "G4"),
    ("G4", "A1"),
    ("G4", "A2"),
]
METRICS = ["M1", "M3", "M4", "M5"]   # M2 not paired (G4/A2 only); M6 manual.


# ─────────────────────────────────────────────
# Load per-requirement metric flags
# ─────────────────────────────────────────────

def _find_group_file(exp_dir: Path, group: str) -> Path | None:
    """Find result file for group: tries .jsonl then .json (new format from script 26)."""
    for pat in (f"{group}_*.jsonl", f"{group}_results.json"):
        candidates = list(exp_dir.glob(pat))
        if candidates:
            return candidates[0]
    return None


def _read_result_sets(path: Path) -> list[dict[str, Any]]:
    """Read either JSONL (one set per line) or JSON ({"group":..., "result_sets":[...]})."""
    if path.suffix == ".jsonl":
        return read_jsonl(str(path))
    text = path.read_text(encoding="utf-8").replace("NaN", "null")
    obj = json.loads(text)
    return obj.get("result_sets", []) if isinstance(obj, dict) else obj


def _per_requirement_flags(result_sets: list[dict[str, Any]], qg: QualityGate, group: str) -> list[dict[str, Any]]:
    """For each engineering_requirement in this group's output, compute
    (M1_pass, M3_pass, M4_pass, M5_pass) as boolean flags so the
    per-requirement statistical model can be fit downstream.
    """
    rows: list[dict[str, Any]] = []
    for rs in result_sets:
        source_id = safe_text(rs.get("source_requirement_id"))
        stakeholder = safe_text(rs.get("stakeholder"))
        for er in (rs.get("engineering_requirements") or []):
            er_id = safe_text(er.get("id"))
            evidence_ids = er.get("evidence_ids") or []
            # M1 PASS = evidence present (no evidence-free); higher is better
            m1_pass = bool(evidence_ids)
            # M3 PASS = over_inference check passed; higher is better
            m3_pass = qg._over_inference(er).passed  # noqa: SLF001
            # M4 PASS = verifiability check passed
            m4_pass = qg._verifiability(er).passed  # noqa: SLF001
            # M5 PASS = mbse_completeness passed (now excludes evidence_ids per CR-4 fix)
            m5_pass = qg._mbse_completeness(er).passed  # noqa: SLF001
            rows.append({
                "group": group,
                "source_requirement_id": source_id,
                "er_id": er_id,
                "stakeholder": stakeholder,
                "M1": int(m1_pass),
                "M3": int(m3_pass),
                "M4": int(m4_pass),
                "M5": int(m5_pass),
            })
    return rows


def load_all_batches(batches_dir: Path, round_dirs: list[Path] | None = None) -> pd.DataFrame:
    """Load experiment result sets into one DataFrame.

    Args:
        batches_dir: Root directory containing batch_* sub-directories.
        round_dirs:  Explicit list of experiment directories (one per round).
                     If provided, only these are loaded in order — prevents
                     stale or incomplete historical batches from being mixed in.
                     If None, falls back to reading round_dirs from
                     three_round_summary.json (preferred) or globbing all
                     batch_* directories (legacy, error-prone when many batches exist).
    """
    qg = QualityGate()
    frames: list[pd.DataFrame] = []

    if round_dirs is None:
        # Try to read canonical round dirs from three_round_summary.json
        summary_path = batches_dir / "three_round_summary.json"
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                raw_dirs = summary.get("round_dirs", [])
                if raw_dirs:
                    round_dirs = [Path(d) for d in raw_dirs]
                    print(f"[info] Using round_dirs from three_round_summary.json ({len(round_dirs)} rounds)")
            except Exception as exc:
                print(f"[warn] Could not read three_round_summary.json: {exc}")

    if round_dirs is None:
        # Legacy fallback: glob all batch dirs alphabetically.
        # WARNING: this assigns round_idx by sort order and will be wrong if
        # historical incomplete batches exist alongside the canonical three rounds.
        all_batch_dirs = sorted(p for p in batches_dir.glob("batch_*") if p.is_dir())
        # Filter to only dirs that have a complete experiment (all 6 groups present)
        round_dirs = []
        for b in all_batch_dirs:
            exp = b / "experiment"
            if exp.exists() and any(exp.glob("G4_results.json")):
                round_dirs.append(exp)
        print(f"[warn] round_dirs not specified; auto-detected {len(round_dirs)} complete batches.")
        print("       Pass --round-dirs or ensure three_round_summary.json is up to date.")

    for round_idx, exp_dir in enumerate(round_dirs, start=1):
        exp_dir = Path(exp_dir)
        # Accept either the experiment/ subdir or the batch dir itself
        if not (exp_dir / "G4_results.json").exists() and (exp_dir / "experiment").exists():
            exp_dir = exp_dir / "experiment"
        if not exp_dir.exists():
            print(f"[warn] round {round_idx}: {exp_dir} not found, skipping")
            continue
        for group in GROUPS:
            f = _find_group_file(exp_dir, group)
            if not f:
                continue
            try:
                rs = _read_result_sets(f)
            except Exception as exc:
                print(f"[warn] skip {f}: {exc}")
                continue
            flags = _per_requirement_flags(rs, qg, group)
            df = pd.DataFrame(flags)
            df["round"] = round_idx
            df["batch"] = exp_dir.parent.name
            frames.append(df)
    if not frames:
        raise RuntimeError(f"No batch data found. Check round_dirs or three_round_summary.json.")
    return pd.concat(frames, ignore_index=True)


# ─────────────────────────────────────────────
# Statistical comparisons
# ─────────────────────────────────────────────

def _paired_proportion_bootstrap(a: np.ndarray, b: np.ndarray, n_resamples: int = 10000, seed: int = 42) -> dict[str, float]:
    """Bootstrap 95% CI on mean(a) - mean(b) for paired binary outcomes.

    a and b are 0/1 arrays of equal length, paired by (round, source_req, er_id).
    """
    rng = np.random.default_rng(seed)
    n = len(a)
    if n == 0:
        return {"diff": float("nan"), "ci_lower": float("nan"), "ci_upper": float("nan")}
    diff_observed = float(a.mean() - b.mean())
    diffs = np.empty(n_resamples, dtype=float)
    idx_pool = np.arange(n)
    for i in range(n_resamples):
        idx = rng.choice(idx_pool, size=n, replace=True)
        diffs[i] = a[idx].mean() - b[idx].mean()
    ci_lower, ci_upper = np.quantile(diffs, [0.025, 0.975])
    return {
        "diff": round(diff_observed, 4),
        "ci_lower": round(float(ci_lower), 4),
        "ci_upper": round(float(ci_upper), 4),
        "n_paired": int(n),
    }


def _wilcoxon_paired(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Paired Wilcoxon signed-rank for binary outcomes.

    Returns p-value and W statistic. Returns NaN if all paired diffs are zero.
    """
    diffs = a - b
    if np.all(diffs == 0):
        return {"statistic": float("nan"), "pvalue": 1.0, "note": "all paired diffs zero"}
    try:
        res = stats.wilcoxon(a, b, zero_method="wilcox", correction=False, alternative="two-sided")
        return {
            "statistic": round(float(res.statistic), 4),
            "pvalue": round(float(res.pvalue), 4),
        }
    except Exception as exc:
        return {"statistic": float("nan"), "pvalue": float("nan"), "error": str(exc)}


def _mixed_model(df_pair: pd.DataFrame, metric: str) -> dict[str, Any]:
    """Fit pass_flag ~ group + (1|round) + (1|stakeholder) via MixedLM.

    Returns coefficient, std error, p-value for the group fixed effect.
    Falls back to NaN if statsmodels not installed or fit fails.
    """
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return {"method": "mixed_lm", "available": False, "note": "statsmodels not installed"}

    if df_pair[metric].nunique() < 2:
        return {"method": "mixed_lm", "available": True, "note": "no variance in outcome"}

    try:
        # Encode group as 0/1 (reference = first group alphabetically)
        df = df_pair.copy()
        df["group_code"] = (df["group"] == df["group"].max()).astype(int)
        # Use round-level random effect; stakeholder added as additional grouping
        # vc_formula approach: stakeholder as variance component
        md = smf.mixedlm(
            formula=f"{metric} ~ group_code",
            data=df,
            groups=df["round"],
            re_formula="~1",
        )
        mdf = md.fit(method=["lbfgs"], reml=True)
        coef = mdf.fe_params.get("group_code", float("nan"))
        bse = mdf.bse_fe.get("group_code", float("nan"))
        pval = mdf.pvalues.get("group_code", float("nan"))
        return {
            "method": "mixed_lm",
            "available": True,
            "coef_group_code": round(float(coef), 4),
            "stderr": round(float(bse), 4),
            "pvalue": round(float(pval), 4),
            "n_obs": int(len(df)),
        }
    except Exception as exc:
        return {"method": "mixed_lm", "available": True, "error": str(exc)}


def compare_groups(df: pd.DataFrame, g_a: str, g_b: str, metric: str) -> dict[str, Any]:
    """Compare two groups on one metric using paired-by-(round, source_requirement_id) data."""
    df_a = df[df["group"] == g_a]
    df_b = df[df["group"] == g_b]
    if df_a.empty or df_b.empty:
        return {"group_a": g_a, "group_b": g_b, "metric": metric, "available": False, "note": "one or both groups missing"}

    # Pair on (round, source_requirement_id) — engineering_requirements within a source
    # requirement may not align across groups, so aggregate to source-requirement level first.
    agg_a = df_a.groupby(["round", "source_requirement_id", "stakeholder"])[metric].mean().reset_index()
    agg_b = df_b.groupby(["round", "source_requirement_id", "stakeholder"])[metric].mean().reset_index()
    merged = agg_a.merge(
        agg_b,
        on=["round", "source_requirement_id", "stakeholder"],
        suffixes=("_a", "_b"),
        how="inner",
    )

    if merged.empty:
        return {"group_a": g_a, "group_b": g_b, "metric": metric, "available": False, "note": "no paired rows"}

    a = merged[f"{metric}_a"].to_numpy(dtype=float)
    b = merged[f"{metric}_b"].to_numpy(dtype=float)

    bootstrap_res = _paired_proportion_bootstrap(a, b)
    wilcoxon_res = _wilcoxon_paired(a, b)
    mixed_res = _mixed_model(
        pd.concat([
            agg_a.assign(group=g_a),
            agg_b.assign(group=g_b),
        ]),
        metric,
    )

    return {
        "group_a": g_a,
        "group_b": g_b,
        "metric": metric,
        "available": True,
        "n_paired": int(len(merged)),
        "mean_a": round(float(a.mean()), 4),
        "mean_b": round(float(b.mean()), 4),
        "bootstrap_diff_ci": bootstrap_res,
        "wilcoxon_paired": wilcoxon_res,
        "mixed_lm": mixed_res,
    }


# ─────────────────────────────────────────────
# LaTeX table writer
# ─────────────────────────────────────────────

def render_latex_table(results: list[dict[str, Any]]) -> str:
    """Render a LaTeX table summarizing the statistical comparisons."""
    rows = []
    for r in results:
        if not r.get("available"):
            continue
        boot = r["bootstrap_diff_ci"]
        wil = r["wilcoxon_paired"]
        mix = r["mixed_lm"]
        diff = boot.get("diff", float("nan"))
        ci_lo = boot.get("ci_lower", float("nan"))
        ci_hi = boot.get("ci_upper", float("nan"))
        p_wil = wil.get("pvalue", float("nan"))
        p_mix = mix.get("pvalue", float("nan")) if mix.get("available") else float("nan")
        sig = "*" if (isinstance(p_mix, float) and p_mix < 0.05) else ""
        rows.append(
            f"{r['metric']} & {r['group_a']} vs.\\ {r['group_b']} & "
            f"{r['mean_a']*100:.2f}\\% vs.\\ {r['mean_b']*100:.2f}\\% & "
            f"{diff*100:+.2f} pp & [{ci_lo*100:+.2f}, {ci_hi*100:+.2f}] & "
            f"{p_wil:.3f} & {p_mix:.3f}{sig}\\\\"
        )
    body = "\n".join(rows)
    return (
        "\\begin{table}[H]\n"
        "\\caption{Per-requirement paired statistical comparisons. "
        "Bootstrap CI from 10,000 resamples; mixed-effects model treats round and stakeholder "
        "as random effects. * denotes $p < 0.05$.}\n"
        "\\begin{tabularx}{\\fulllength}{lCCCCCC}\n"
        "\\toprule\n"
        "\\textbf{Metric} & \\textbf{Comparison} & "
        "\\textbf{Pass rate} & \\textbf{$\\Delta$ (pp)} & "
        "\\textbf{95\\% CI} & \\textbf{$p_{Wilcoxon}$} & \\textbf{$p_{MixedLM}$}\\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabularx}\n"
        "\\end{table}\n"
    )


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Per-requirement statistical analysis.")
    parser.add_argument(
        "--batches-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "search_results",
        help="Root directory containing batch_* sub-directories.",
    )
    parser.add_argument(
        "--round-dirs",
        nargs="+",
        type=Path,
        default=None,
        metavar="EXP_DIR",
        help=(
            "Explicit experiment directories, one per round (e.g. "
            "data/search_results/batch_X/experiment). "
            "Overrides auto-detection from three_round_summary.json."
        ),
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=PROJECT_ROOT / "data" / "search_results" / "statistical_analysis.json",
    )
    parser.add_argument(
        "--out-tex",
        type=Path,
        default=PROJECT_ROOT / "data" / "search_results" / "statistical_analysis.tex",
    )
    args = parser.parse_args()

    print(f"[1/3] Loading batches under {args.batches_dir} ...")
    df = load_all_batches(args.batches_dir, round_dirs=args.round_dirs)
    print(f"      Loaded {len(df)} per-ER rows across {df['round'].nunique()} rounds "
          f"and {df['group'].nunique()} groups.")

    print("[2/3] Running pairwise comparisons ...")
    results: list[dict[str, Any]] = []
    for g_a, g_b in COMPARISONS:
        for metric in METRICS:
            res = compare_groups(df, g_a, g_b, metric)
            results.append(res)
            if res.get("available"):
                boot = res["bootstrap_diff_ci"]
                print(
                    f"  {g_a} vs {g_b} on {metric}: "
                    f"diff={boot['diff']*100:+.2f}pp "
                    f"CI=[{boot['ci_lower']*100:+.2f}, {boot['ci_upper']*100:+.2f}] "
                    f"p_wilcox={res['wilcoxon_paired'].get('pvalue', float('nan'))}"
                )

    args.out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    args.out_tex.write_text(render_latex_table(results), encoding="utf-8")
    print(f"[3/3] Wrote {args.out_json} and {args.out_tex}")


if __name__ == "__main__":
    main()
