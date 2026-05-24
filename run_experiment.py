# -*- coding: utf-8 -*-
"""
One-click experiment runner.

Runs the full pipeline in order:
  Step 0  Check prerequisites (indexes, .env)
  Step 1  Generate 20 test requirements          (script 20)
  Step 2  Run 4+2 group experiment               (script 21)
  Step 3  Compute M1–M5 metrics                  (script 22)
  Step 4  Export LaTeX / Markdown table          (script 23)
  Step 5  Export case study for G4               (script 24)

Usage:
  python run_experiment.py
  python run_experiment.py --groups G1 G4 A1 A2   # subset of groups
  python run_experiment.py --top-k 4 --skip-gen    # skip requirement generation
  python run_experiment.py --case-index 2          # pick the 3rd G4 result for case study
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 彩色输出 ──────────────────────────────────
try:
    from colorama import Fore, Style, init as _cinit
    _cinit(autoreset=True)
    def _green(s: str) -> str: return f"{Fore.GREEN}{s}{Style.RESET_ALL}"
    def _yellow(s: str) -> str: return f"{Fore.YELLOW}{s}{Style.RESET_ALL}"
    def _red(s: str) -> str: return f"{Fore.RED}{s}{Style.RESET_ALL}"
    def _cyan(s: str) -> str: return f"{Fore.CYAN}{s}{Style.RESET_ALL}"
except ImportError:
    def _green(s): return s
    def _yellow(s): return s
    def _red(s): return s
    def _cyan(s): return s

ALL_GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]

_SEP = "─" * 60


def _step(n: int, title: str) -> None:
    print(f"\n{_cyan(_SEP)}")
    print(_cyan(f"  STEP {n}  {title}"))
    print(_cyan(_SEP))


def _ok(msg: str) -> None:
    print(_green(f"  ✓ {msg}"))


def _warn(msg: str) -> None:
    print(_yellow(f"  ⚠ {msg}"))


def _fail(msg: str) -> None:
    print(_red(f"  ✗ {msg}"))


def _elapsed(t0: float) -> str:
    s = time.time() - t0
    return f"{int(s // 60)}m {s % 60:.1f}s" if s >= 60 else f"{s:.1f}s"


# ─────────────────────────────────────────────
# Step 0: 先决条件检查
# ─────────────────────────────────────────────

def check_prerequisites(cfg) -> bool:
    ok = True

    # 检查 indexes
    for name in ("evidence_units", "source_chunks"):
        idx_dir = cfg.paths.indexes_dir / name
        if not (idx_dir / "faiss.index").exists():
            _fail(f"Index missing: {idx_dir}/faiss.index")
            _fail("Please run:  python scripts/11_build_multigranular_indexes.py")
            ok = False
        else:
            _ok(f"Index found: {name}")

    # 检查 evidence JSONL
    for attr in ("evidence_units_jsonl", "evidence_groups_jsonl"):
        p = getattr(cfg.paths, attr)
        if not Path(p).exists():
            _fail(f"JSONL missing: {p}")
            _fail("Please run:  python scripts/10_convert_docx_to_multigranular_jsonl.py")
            ok = False
        else:
            _ok(f"JSONL found: {Path(p).name}")

    # 检查 API key
    if not cfg.deepseek.enabled:
        _fail("DEEPSEEK_API_KEY not set — LLM steps will fail")
        ok = False
    else:
        _ok("DeepSeek API key found")

    return ok


# ─────────────────────────────────────────────
# Step 1: 生成测试需求
# ─────────────────────────────────────────────

def step_generate_requirements(cfg, overwrite: bool = False) -> list:
    from cooling_rag_mg.requirement_generator import generate_test_requirements

    output_path = cfg.paths.processed_dir / "test_requirements.jsonl"
    if output_path.exists() and not overwrite:
        _warn(f"test_requirements.jsonl already exists — skipping generation")
        _warn("Use --overwrite to regenerate")
        from cooling_rag_mg.jsonl import read_jsonl
        reqs = read_jsonl(str(output_path))
        _ok(f"Loaded {len(reqs)} existing requirements")
        return reqs

    reqs = generate_test_requirements(
        evidence_units_path=cfg.paths.evidence_units_jsonl,
        output_path=output_path,
        overwrite=overwrite,
    )
    _ok(f"Generated {len(reqs)} test requirements → {output_path}")
    return reqs


# ─────────────────────────────────────────────
# Step 2: 运行实验
# ─────────────────────────────────────────────

def step_run_experiment(cfg, groups: list[str], top_k: int) -> Path:
    from cooling_rag_mg.engineering_requirement_agent import generate_engineering_requirements
    from cooling_rag_mg.evidence_pack import make_batch_dir
    from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
    from cooling_rag_mg.pipeline import make_services, run_requirements_with_services
    from cooling_rag_mg.quality_gate import QualityGate
    from cooling_rag_mg.sysml_exporter import export_batch

    # 复用 script 21 的所有函数（动态 import）
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(
        "exp21",
        PROJECT_ROOT / "scripts" / "21_run_experiment.py",
    )
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    test_req_path = cfg.paths.processed_dir / "test_requirements.jsonl"
    if not test_req_path.exists():
        raise FileNotFoundError(f"Test requirements not found: {test_req_path}")

    reqs = read_jsonl(str(test_req_path))
    print(f"  Loaded {len(reqs)} test requirements")

    batch_dir = make_batch_dir(cfg.paths.search_results_dir)
    exp_dir = batch_dir / "experiment"
    exp_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {exp_dir}")

    if "G1" in groups:
        t = time.time()
        print(f"\n  {_cyan('[G1]')} Direct LLM …")
        mod._run_g1(reqs, exp_dir, cfg)
        _ok(f"G1 done ({_elapsed(t)})")

    if "G2" in groups:
        t = time.time()
        print(f"\n  {_cyan('[G2]')} Flat RAG …")
        mod._run_g2(reqs, exp_dir, cfg, top_k)
        _ok(f"G2 done ({_elapsed(t)})")

    for group, with_qg, with_profile in [
        ("G3", False, True),
        ("G4", True,  True),
        ("A1", False, True),
        ("A2", True,  False),
    ]:
        if group not in groups:
            continue
        t = time.time()
        label_map = {
            "G3": "Multi-granular RAG (no QG)",
            "G4": "Proposed (multi-RAG + QG + SysML)",
            "A1": "Ablation — no quality gate",
            "A2": "Ablation — no profile scoring",
        }
        print(f"\n  {_cyan(f'[{group}]')} {label_map[group]} …")
        mod._run_pipeline_group(
            group, reqs, exp_dir, cfg,
            with_quality_gate=with_qg,
            with_profile_scoring=with_profile,
            top_k=top_k,
        )
        _ok(f"{group} done ({_elapsed(t)})")

    return exp_dir


# ─────────────────────────────────────────────
# Step 3: 计算指标
# ─────────────────────────────────────────────

def step_compute_metrics(exp_dir: Path) -> list:
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(
        "exp22",
        PROJECT_ROOT / "scripts" / "22_compute_metrics.py",
    )
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    from cooling_rag_mg.quality_gate import QualityGate
    qg = QualityGate()
    rows = []
    for group in ALL_GROUPS:
        result_sets = mod._load_group(exp_dir, group)
        if not result_sets:
            continue
        reqs = mod._flatten_requirements(result_sets)
        rows.append({
            "group":  group,
            "n_sets": len(result_sets),
            "n_reqs": len(reqs),
            "m1": mod._m1_evidence_free_rate(reqs),
            "m2": mod._m2_qg_pass_rate(reqs),
            "m3": mod._m3_over_inference_rate(reqs, qg),
            "m4": mod._m4_verifiability_score(reqs, qg),
            "m5": mod._m5_mbse_completeness(reqs, qg),
        })

    mod._print_table(rows)

    import json
    metrics_path = exp_dir / "metrics_summary.json"
    metrics_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    _ok(f"metrics_summary.json → {metrics_path}")

    mod._print_m6_sampling(exp_dir, group="G4", n=20)
    return rows


# ─────────────────────────────────────────────
# Step 4: 导出 LaTeX 表格
# ─────────────────────────────────────────────

def step_export_table(exp_dir: Path, rows: list) -> None:
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(
        "exp23",
        PROJECT_ROOT / "scripts" / "23_export_latex_table.py",
    )
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    latex = mod.generate_latex_table(rows)
    md    = mod.generate_markdown_table(rows)

    (exp_dir / "table_metrics.tex").write_text(latex, encoding="utf-8")
    (exp_dir / "table_metrics.md").write_text(md, encoding="utf-8")

    print("\n" + md)
    _ok(f"table_metrics.tex / .md → {exp_dir}")


# ─────────────────────────────────────────────
# Step 5: 导出案例研究
# ─────────────────────────────────────────────

def step_export_case_study(exp_dir: Path, index: int = 0) -> None:
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(
        "exp24",
        PROJECT_ROOT / "scripts" / "24_export_case_study.py",
    )
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    from cooling_rag_mg.jsonl import read_jsonl
    from cooling_rag_mg.text_utils import safe_text
    import json

    candidates = list(exp_dir.glob("G4_*.jsonl"))
    if not candidates:
        _warn("No G4 results found — skipping case study export")
        return

    result_sets = read_jsonl(str(candidates[0]))
    if not result_sets:
        _warn("G4 results file is empty — skipping case study export")
        return

    idx = min(index, len(result_sets) - 1)
    rs = result_sets[idx]
    set_id = safe_text(rs.get("requirement_set_id")) or f"G4-{idx}"

    md = mod.generate_case_study_md(rs)
    md_path   = exp_dir / f"case_study_{set_id}.md"
    json_path = exp_dir / f"case_study_{set_id}.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(rs, ensure_ascii=False, indent=2), encoding="utf-8")

    _ok(f"case_study_{set_id}.md → {exp_dir}")


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-click full experiment runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--groups", nargs="+", default=ALL_GROUPS, choices=ALL_GROUPS,
        help="Experiment groups to run (default: all)",
    )
    parser.add_argument("--top-k", type=int, default=4,
                        help="Evidence items per sub-requirement (default: 4)")
    parser.add_argument("--skip-gen", action="store_true",
                        help="Skip requirement generation (use existing file)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-generate test requirements even if file exists")
    parser.add_argument("--case-index", type=int, default=0,
                        help="Index of G4 result set for case study (default: 0)")
    parser.add_argument("--skip-steps", nargs="+", type=int, default=[],
                        choices=[1, 2, 3, 4, 5],
                        help="Step numbers to skip (e.g. --skip-steps 1 5)")
    parser.add_argument("--exp-dir", default=None,
                        help="Use existing experiment directory (skips step 2)")
    args = parser.parse_args()

    t_total = time.time()

    from cooling_rag_mg.config import get_config
    cfg = get_config()

    # ── Step 0: prerequisites ─────────────────
    _step(0, "Checking prerequisites")
    if not check_prerequisites(cfg):
        _fail("Prerequisites not met. Aborting.")
        sys.exit(1)
    _ok("All prerequisites OK")

    # ── Step 1: generate test requirements ───
    if 1 not in args.skip_steps and not args.skip_gen:
        _step(1, "Generating test requirements")
        t = time.time()
        step_generate_requirements(cfg, overwrite=args.overwrite)
        _ok(f"Step 1 complete ({_elapsed(t)})")
    else:
        _warn("Step 1 skipped (--skip-gen or --skip-steps 1)")

    # ── Step 2: run experiment ────────────────
    if args.exp_dir:
        exp_dir = Path(args.exp_dir)
        _warn(f"Step 2 skipped — using existing exp_dir: {exp_dir}")
    elif 2 not in args.skip_steps:
        _step(2, f"Running experiment (groups={args.groups}, top-k={args.top_k})")
        t = time.time()
        exp_dir = step_run_experiment(cfg, args.groups, args.top_k)
        _ok(f"Step 2 complete ({_elapsed(t)})")
    else:
        batches = sorted(cfg.paths.search_results_dir.glob("batch_*/experiment"))
        if not batches:
            _fail("--skip-steps 2 requires an existing experiment batch. None found.")
            sys.exit(1)
        exp_dir = batches[-1]
        _warn(f"Step 2 skipped — using latest: {exp_dir}")

    # ── Step 3: compute metrics ───────────────
    if 3 not in args.skip_steps:
        _step(3, "Computing M1–M5 metrics")
        t = time.time()
        rows = step_compute_metrics(exp_dir)
        _ok(f"Step 3 complete ({_elapsed(t)})")
    else:
        import json
        mp = exp_dir / "metrics_summary.json"
        rows = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else []
        _warn("Step 3 skipped")

    # ── Step 4: export table ──────────────────
    if 4 not in args.skip_steps and rows:
        _step(4, "Exporting LaTeX / Markdown table")
        t = time.time()
        step_export_table(exp_dir, rows)
        _ok(f"Step 4 complete ({_elapsed(t)})")
    else:
        _warn("Step 4 skipped")

    # ── Step 5: export case study ─────────────
    if 5 not in args.skip_steps and "G4" in args.groups:
        _step(5, f"Exporting G4 case study (index={args.case_index})")
        t = time.time()
        step_export_case_study(exp_dir, index=args.case_index)
        _ok(f"Step 5 complete ({_elapsed(t)})")
    else:
        _warn("Step 5 skipped (G4 not in groups or --skip-steps 5)")

    # ── 总结 ──────────────────────────────────
    print(f"\n{_cyan(_SEP)}")
    print(_green(f"  ALL DONE  Total time: {_elapsed(t_total)}"))
    print(_cyan(f"  Results → {exp_dir}"))
    print(_cyan(_SEP))


if __name__ == "__main__":
    main()
