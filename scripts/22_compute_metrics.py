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
import math
import random
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.text_utils import safe_text

# Shared sample cache so multiple groups (e.g. G4 and A2) sample the SAME
# source_requirement_ids — this makes the M6 comparison paired rather than
# independent.  Keyed by exp_dir to avoid leakage across runs in the same
# Python process.
_M6_SAMPLE_CACHE: dict[Path, list[str]] = {}


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


def _m1_evidence_free_rate(reqs: list[dict[str, Any]], group: str = "") -> float:
    # G1 is a no-evidence baseline by design; M1=1.0 is a trivial constant, not a measurement.
    if group == "G1" or not reqs:
        return float("nan")
    empty = sum(1 for r in reqs if not (r.get("evidence_ids") or []))
    return round(empty / len(reqs), 4)


def _m2_qg_pass_rate(reqs: list[dict[str, Any]], group: str = "") -> float:
    """Only meaningful for groups that explicitly run the quality gate (G4, A2)."""
    if group not in {"G4", "A2"}:
        return float("nan")
    qg_reqs = [r for r in reqs if r.get("quality_gate_report")]
    if not qg_reqs:
        return float("nan")
    passed = sum(1 for r in qg_reqs
                 if (r.get("quality_gate_report") or {}).get("overall_passed"))
    return round(passed / len(qg_reqs), 4)


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


def _m5_mbse_completeness(reqs: list[dict[str, Any]], qg: QualityGate, group: str = "") -> float:
    # G1 has all structural fields but evidence_ids=[] by design; M5=0 would reflect
    # the baseline constraint rather than structural quality — exclude from comparison.
    if group == "G1" or not reqs:
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


def _m6_from_review_file(exp_dir: Path) -> dict:
    """Read M6_review.json and compute three M6 sub-metrics.

    Returns dict with keys M6_decomp, M6_trace, M6_gap (floats or nan).
      M6_decomp: decomposition_correct==True / ERs with judged decomposition
      M6_trace:  traceability_correct==True / ERs with evidence AND judged traceability
      M6_gap:    (decomp_correct AND no evidence) / ERs with decomp_correct==True
    """
    nan = float("nan")
    review_path = exp_dir / "M6_review.json"
    if not review_path.exists():
        return {"M6_decomp": nan, "M6_trace": nan, "M6_gap": nan}
    data = json.loads(review_path.read_text(encoding="utf-8"))

    decomp_judged = decomp_correct = 0
    trace_judged = trace_correct = 0
    gap_denom = gap_num = 0

    for rs in data.get("requirement_sets", []):
        for er in rs.get("engineering_requirements", []):
            rev = er.get("review", {})
            has_ev = bool(er.get("evidence"))
            d_val = rev.get("decomposition_correct")
            t_val = rev.get("traceability_correct")

            if d_val is not None:
                decomp_judged += 1
                if d_val is True:
                    decomp_correct += 1
                    gap_denom += 1
                    if not has_ev:
                        gap_num += 1

            if has_ev and t_val is not None:
                trace_judged += 1
                if t_val is True:
                    trace_correct += 1

    return {
        "M6_decomp": round(decomp_correct / decomp_judged, 4) if decomp_judged else nan,
        "M6_trace":  round(trace_correct / trace_judged, 4) if trace_judged else nan,
        "M6_gap":    round(gap_num / gap_denom, 4) if gap_denom else nan,
    }


def _stratified_sample_source_ids(
    exp_dir: Path,
    group: str,
    n: int,
    seed: int = 42,
) -> list[str]:
    """Pick `n` source_requirement_ids stratified by (stakeholder, engineering_type).

    The result is cached per `exp_dir` so subsequent calls for other groups
    (e.g. A2 after G4) use the SAME ids, enabling paired comparison.

    Stakeholder is read from the result_set; engineering_type is the most
    common requirement_type among the set's engineering_requirements.
    """
    if exp_dir in _M6_SAMPLE_CACHE:
        return _M6_SAMPLE_CACHE[exp_dir]

    rng = random.Random()
    rng.seed(seed)

    result_sets = _load_group(exp_dir, group)
    if not result_sets:
        _M6_SAMPLE_CACHE[exp_dir] = []
        return []

    # Build (source_id, stakeholder, engineering_type) tuples
    rows: list[tuple[str, str, str]] = []
    for rs in result_sets:
        src_id = safe_text(rs.get("source_requirement_id") or rs.get("requirement_set_id"))
        if not src_id:
            continue
        stakeholder = safe_text(rs.get("stakeholder"))
        types: dict[str, int] = {}
        for er in rs.get("engineering_requirements", []) or []:
            t = safe_text(er.get("requirement_type")) or "other"
            types[t] = types.get(t, 0) + 1
        eng_type = max(types, key=types.get) if types else "other"
        rows.append((src_id, stakeholder, eng_type))

    if not rows:
        _M6_SAMPLE_CACHE[exp_dir] = []
        return []

    n = min(n, len(rows))

    # Group by (stakeholder, engineering_type)
    strata: dict[tuple[str, str], list[str]] = {}
    for src_id, stk, et in rows:
        strata.setdefault((stk, et), []).append(src_id)

    # Shuffle each stratum deterministically
    for key in strata:
        rng.shuffle(strata[key])

    # Proportional allocation with largest-remainder method
    total = len(rows)
    alloc: dict[tuple[str, str], int] = {}
    remainders: list[tuple[float, tuple[str, str]]] = []
    assigned = 0
    for key, members in strata.items():
        raw = n * len(members) / total
        base = int(math.floor(raw))
        alloc[key] = base
        remainders.append((raw - base, key))
        assigned += base
    # Distribute the leftover one-by-one to strata with the largest remainders
    remainders.sort(key=lambda x: (-x[0], x[1]))
    leftover = n - assigned
    i = 0
    while leftover > 0 and remainders:
        _, key = remainders[i % len(remainders)]
        if alloc[key] < len(strata[key]):
            alloc[key] += 1
            leftover -= 1
        i += 1
        if i > len(remainders) * 4:  # safety
            break

    sampled: list[str] = []
    for key, take in alloc.items():
        sampled.extend(strata[key][:take])

    # Final top-up if rounding under-allocated (e.g. strata exhausted)
    if len(sampled) < n:
        seen = set(sampled)
        pool = [src for src, _, _ in rows if src not in seen]
        rng.shuffle(pool)
        sampled.extend(pool[: n - len(sampled)])

    sampled = sampled[:n]
    _M6_SAMPLE_CACHE[exp_dir] = sampled
    return sampled


def _print_m6_sampling(exp_dir: Path, group: str = "G4", n: int = 20) -> None:
    random.seed(42)
    # If a review file exists with any judged entries, report M6 from it.
    m6 = _m6_from_review_file(exp_dir)
    decomp = m6["M6_decomp"]
    if decomp == decomp:  # not nan — at least some entries reviewed
        data = json.loads((exp_dir / "M6_review.json").read_text(encoding="utf-8"))
        total = data.get("total_ers", 0)
        decomp_judged = sum(
            1 for rs in data.get("requirement_sets", [])
            for er in rs.get("engineering_requirements", [])
            if er.get("review", {}).get("decomposition_correct") is not None
        )
        trace = m6["M6_trace"]
        gap = m6["M6_gap"]
        trace_str = f"{trace * 100:.1f}%" if trace == trace else "n/a (no ERs with evidence judged)"
        gap_str = f"{gap * 100:.1f}%" if gap == gap else "n/a"
        print(f"\nM6 (from M6_review.json)  [{decomp_judged}/{total} ERs reviewed]")
        print(f"  M6_decomp  Decomposition correctness : {decomp * 100:.1f}%")
        print(f"  M6_trace   Traceability precision    : {trace_str}")
        print(f"  M6_gap     Evidence gap rate         : {gap_str}")
        return

    # No review file yet — generate a sampling template via stratified sample.
    result_sets = _load_group(exp_dir, group)
    if not result_sets:
        return

    # Stratified pick of source_requirement_ids; shared across groups in the
    # same exp_dir so G4 and A2 (etc.) review the SAME requirements.
    sampled_src_ids = _stratified_sample_source_ids(exp_dir, group, n)
    src_id_set = set(sampled_src_ids)

    # Pull the engineering requirements belonging to the sampled set
    reqs = []
    for rs in result_sets:
        if safe_text(rs.get("source_requirement_id")) in src_id_set:
            for er in rs.get("engineering_requirements", []) or []:
                er = dict(er)
                er["_set_id"] = rs.get("requirement_set_id", "")
                er["_source_requirement_id"] = rs.get("source_requirement_id", "")
                reqs.append(er)
        if len(src_id_set) and len(reqs) and len({r["_source_requirement_id"] for r in reqs}) >= len(sampled_src_ids):
            # have collected all sampled sets; keep collecting their ERs (loop continues anyway)
            pass

    out = []
    for i, r in enumerate(reqs, start=1):
        out.append({
            "index": i,
            "requirement_id": safe_text(r.get("id")),
            "source_requirement_id": safe_text(r.get("_source_requirement_id")),
            "shall_statement": safe_text(r.get("shall_statement"))[:200],
            "evidence_ids": r.get("evidence_ids") or [],
            "support_status": safe_text(r.get("support_status")),
            "M6_human_judgement": {
                "traceability_correct": None,
                "notes": "",
            },
        })
    sampling_path = exp_dir / "M6_sampling_template.json"
    sampling_path.write_text(
        json.dumps(
            {
                "sampling_method": "stratified_by_stakeholder_and_engineering_type",
                "seed": 42,
                "n_source_requirements": len(sampled_src_ids),
                "sampled_source_ids": sampled_src_ids,
                "items": out,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nM6 sampling template ({len(sampled_src_ids)} src reqs, {len(out)} ERs) saved -> {sampling_path}")
    print("Use 'm6_review_ui.py' (streamlit run scripts/m6_review_ui.py --server.port 8502)")
    print("or fill 'traceability_correct' manually, then re-run this script.")


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
            "m1": _m1_evidence_free_rate(reqs, group),
            "m2": _m2_qg_pass_rate(reqs, group),
            "m3": _m3_over_inference_rate(reqs, qg),
            "m4": _m4_verifiability_score(reqs, qg),
            "m5": _m5_mbse_completeness(reqs, qg, group),
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
