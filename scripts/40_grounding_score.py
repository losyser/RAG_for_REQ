# scripts/40_grounding_score.py
# -*- coding: utf-8 -*-
"""动作 A：证据-需求语义契合度（grounding score）。

读取已有 batch 的 G2/G3/G4 结果，对每条有证据的 ER 算 (shall, evidence) 契合度，
按 source_requirement_id 聚合，G2 vs G3 / G2 vs G4 配对检验。

用法：
  python scripts/40_grounding_score.py                      # reranker 分，自动找完整 batch
  python scripts/40_grounding_score.py --llm qwen           # 追加 Qwen 蕴含分
  python scripts/40_grounding_score.py --batches DIR1 DIR2  # 指定 batch
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.grounding import (
    LLMEntailmentScorer, RerankerScorer, load_evidence_text_map,
    paired_compare, score_result_sets,
)


def _find_batches(search_dir: Path) -> list[Path]:
    out = []
    for exp in sorted(search_dir.glob("batch_*/experiment")):
        if (exp / "G2_results.json").exists() and (exp / "G3_results.json").exists():
            out.append(exp)
    return out


def _load_sets(exp_dir: Path, group: str) -> list:
    p = exp_dir / f"{group}_results.json"
    return json.loads(p.read_text(encoding="utf-8")).get("result_sets", []) if p.exists() else []


def _scored_by_group(exp_dirs, text_map, scorer, groups):
    """返回 {group: {f'{batch}::{src}': score}}。"""
    merged = {g: {} for g in groups}
    for exp in exp_dirs:
        batch = exp.parent.name
        for g in groups:
            per_src = score_result_sets(_load_sets(exp, g), text_map, scorer)
            for src, sc in per_src.items():
                merged[g][f"{batch}::{src}"] = sc
    return merged


def _latex(label, res) -> str:
    return (f"{label} & {res['mean_a']:.3f} & {res['mean_b']:.3f} & "
            f"{res['mean_diff']:+.3f} & [{res['ci_low']:+.3f}, {res['ci_high']:+.3f}] & "
            f"{res['pvalue']:.3f} \\\\")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="*", help="experiment 目录；缺省自动找完整 batch")
    ap.add_argument("--llm", choices=["qwen", "ernie"], help="追加 LLM 蕴含分（默认仅 reranker）")
    args = ap.parse_args()

    cfg = get_config()
    text_map = load_evidence_text_map(cfg.paths.evidence_units_jsonl)

    exp_dirs = [Path(b) for b in args.batches] if args.batches else _find_batches(cfg.paths.search_results_dir)
    if not exp_dirs:
        print("未找到含 G2/G3 的 batch。先运行 scripts/26_run_three_rounds.py。")
        sys.exit(1)
    print(f"[grounding] {len(exp_dirs)} 个 batch")

    groups = ["G2", "G3", "G4"]
    scorers = {"reranker": RerankerScorer(device=cfg.model.device)}
    if args.llm:
        c = cfg.qwen if args.llm == "qwen" else cfg.ernie
        if not c.enabled:
            print(f"{args.llm} 未配置 API key（.env）。"); sys.exit(1)
        scorers[args.llm] = LLMEntailmentScorer(c.make_client(), model=c.model, temperature=c.temperature)

    out: dict = {"batches": [e.parent.name for e in exp_dirs], "scorers": {}}
    latex_lines = []
    for sname, scorer in scorers.items():
        by_group = _scored_by_group(exp_dirs, text_map, scorer, groups)
        cmp_g3 = paired_compare(by_group["G2"], by_group["G3"])
        cmp_g4 = paired_compare(by_group["G2"], by_group["G4"])
        out["scorers"][sname] = {"G2_vs_G3": cmp_g3, "G2_vs_G4": cmp_g4,
                                 "group_means": {g: (sum(by_group[g].values()) / len(by_group[g])
                                                     if by_group[g] else float("nan")) for g in groups}}
        latex_lines.append(f"% {sname}")
        latex_lines.append(_latex(f"{sname} G2$\\to$G3", cmp_g3))
        latex_lines.append(_latex(f"{sname} G2$\\to$G4", cmp_g4))
        print(f"[{sname}] G2={out['scorers'][sname]['group_means']['G2']:.3f} "
              f"G3={out['scorers'][sname]['group_means']['G3']:.3f} "
              f"G2vsG3 diff={cmp_g3['mean_diff']:+.3f} p={cmp_g3['pvalue']:.3f} "
              f"CI[{cmp_g3['ci_low']:+.3f},{cmp_g3['ci_high']:+.3f}] n={cmp_g3['n_pairs']}")

    out_json = cfg.paths.search_results_dir / "grounding_score.json"
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_tex = cfg.paths.search_results_dir / "grounding_score_table.tex"
    header = ("% grounding score: mean_A mean_B diff CI p\n"
              "\\begin{tabular}{lccccc}\n\\toprule\n"
              "Comparison & A & B & $\\Delta$ & 95\\% CI & $p$\\\\\n\\midrule\n")
    out_tex.write_text(header + "\n".join(latex_lines) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")
    print(f"-> {out_json}\n-> {out_tex}")


if __name__ == "__main__":
    main()
