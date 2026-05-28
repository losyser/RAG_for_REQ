# -*- coding: utf-8 -*-
"""
Run the G4 pipeline on the stress-test requirement pool (ST001–ST030)
and compute M1–M5 metrics.

This evaluates whether the system generalises beyond the DeepSeek-generated
dev pool to requirements produced by an independent model (Qwen) with
deliberately injected deficiency patterns.

Prerequisites:
  python scripts/37_generate_stress_test_requirements.py   # generate ST pool
  python scripts/11_build_multigranular_indexes.py         # indexes exist

Usage:
  python scripts/38_run_stress_test.py
  python scripts/38_run_stress_test.py --top-k 4 --out-dir data/search_results/stress_test
  python scripts/38_run_stress_test.py --device cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg import seed_everything
from cooling_rag_mg.config import get_config
from cooling_rag_mg.experiment_runner import (
    compute_metrics,
    run_pipeline_group,
    save_experiment_results,
)
from cooling_rag_mg.jsonl import read_jsonl

STRESS_POOL = PROJECT_ROOT / "data" / "processed" / "stress_test_requirements.jsonl"


def _load_requirements(path: Path) -> list[dict]:
    rows = read_jsonl(str(path))
    # Drop any rows that failed generation
    valid = [r for r in rows if r.get("requirement_text")]
    if not valid:
        raise FileNotFoundError(
            f"No valid requirements found in {path}. "
            "Run scripts/37_generate_stress_test_requirements.py first."
        )
    return valid


def main() -> None:
    parser = argparse.ArgumentParser(description="Run G4 on stress-test requirements")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument(
        "--out-dir",
        default=str(
            PROJECT_ROOT / "data" / "search_results"
            / f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default=None,
        help="Embedding device override. Use cpu if CUDA memory is tight.",
    )
    args = parser.parse_args()

    if args.device:
        if args.device == "auto":
            os.environ.pop("DEVICE", None)
        else:
            os.environ["DEVICE"] = args.device

    seed_everything(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    requirements = _load_requirements(STRESS_POOL)
    print(f"Loaded {len(requirements)} stress-test requirements from {STRESS_POOL.name}")

    cfg = get_config()
    print(f"Running G4 pipeline (top_k={args.top_k}, device={cfg.model.device})...")
    g4_results = run_pipeline_group(
        "G4",
        requirements,
        cfg,
        with_quality_gate=True,
        with_profile_scoring=True,
        top_k=args.top_k,
    )

    results_by_group = {"G4": g4_results}
    metrics_rows = compute_metrics(results_by_group)
    exp_dir = save_experiment_results(
        results_by_group,
        metrics_rows,
        results_root=out_dir,
        top_k=args.top_k,
        n_requirements=len(requirements),
    )

    g4_metrics = next((r for r in metrics_rows if r.get("group") == "G4"), {})
    summary = {
        "group": "G4",
        "pool": "stress_test (Qwen-Max, 7 deficiency patterns)",
        "n_source_requirements": len(requirements),
        "top_k": args.top_k,
        "device": cfg.model.device,
        "seed": args.seed,
        "metrics": g4_metrics,
    }
    with open(exp_dir / "stress_test_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n── Stress-test results (G4, n={len(requirements)}) ──")
    for k, v in g4_metrics.items():
        if k == "group":
            continue
        print(f"  {k}: {v:.1%}" if isinstance(v, float) else f"  {k}: {v}")
    print(f"\nResults saved -> {exp_dir}")


if __name__ == "__main__":
    main()
