# scripts/59_evaluate_v3.py
"""
v3 实验评估：H_hard 矛盾率（主）+ 4维盲评（辅）

数据：
  data/search_results/exp_v3/rag_v3_results.json   ← RAG v3
  data/search_results/exp_v3/norag_results.json    ← no-RAG 强基线

指标：
  H_hard  矛盾率（RAG v3 vs no-RAG，Wilcoxon 配对检验）
    - claim 抽取：DeepSeek
    - KB 判断：   Qwen（裁判≠生成者）
  4维盲评  completeness / actionability / consistency / verifiability
    - 裁判：Qwen，左右交换取共识
  描述统计：shall数 / 含数字比例 / 有归因比例

输出：
  data/search_results/exp_v3/eval_v3.json        ← 完整结果
  data/search_results/exp_v3/eval_v3_summary.txt  ← 可读摘要

用法：
  python scripts/59_evaluate_v3.py --limit 5    # 冒烟
  python scripts/59_evaluate_v3.py              # 全量（约 90min，需 API）
  python scripts/59_evaluate_v3.py --skip-hhard # 只跑盲评，跳过 H_hard
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.credibility_eval import (
    aggregate_by_source, extract_claims, judge_over_inference,
    score_shall,
)
from cooling_rag_mg.quality_eval import aggregate_quality, consensus_pair
from cooling_rag_mg.quality_judge import DIMS

EXP    = PROJECT_ROOT / "data" / "search_results" / "exp_v3"
IDX    = PROJECT_ROOT / "data" / "indexes" / "evidence_units"
ORIG   = PROJECT_ROOT / "data" / "processed" / "original_requirements_v2.jsonl"

_NUM_RE = re.compile(r"\d")


def _load_results(rag_path: Path, norag_path: Path) -> tuple[dict, dict]:
    with open(rag_path, encoding="utf-8") as f:
        data = json.load(f)
        rs = data["result_sets"] if isinstance(data, dict) else data
        rag = {r["source_requirement_id"]: r for r in rs}
    with open(norag_path, encoding="utf-8") as f:
        data = json.load(f)
        rs = data["result_sets"] if isinstance(data, dict) else data
        norag = {r["source_requirement_id"]: r for r in rs}
    return rag, norag


def _has_attribution(er: dict) -> bool:
    """Check attribution in either evidence_refs or evidence_ids field."""
    return bool(er.get("evidence_refs") or er.get("evidence_ids") or er.get("evidence_citations"))


def _load_orig() -> dict[str, str]:
    with open(ORIG, encoding="utf-8") as f:
        return {json.loads(l)["requirement_id"]: json.loads(l)["requirement_text"]
                for l in f}


def _kb_passages(searcher: HybridIndexSearcher, claim: str, k: int = 5) -> list[str]:
    """Retrieve top-k KB passages for a claim (used as evidence for OI judge)."""
    results = searcher.vector_search(claim, k)
    return [r.get("text", "")[:400] for r in results if r.get("text")]


def _judge_claim_against_kb(
    claim: str, kb_passages: list[str], client, model: str
) -> str:
    """Judge a single claim: support / contradict / not_found."""
    from cooling_rag_mg.llm_cache import cached_completion
    if not kb_passages:
        return "not_found"
    passages_block = "\n".join(f"[P{i+1}] {p}" for i, p in enumerate(kb_passages))
    prompt = (
        "你是船舶冷却水系统专家。判断以下【工程主张】是否被【知识库段落】支持、矛盾或未提及。\n\n"
        f"工程主张：{claim}\n\n"
        f"知识库段落：\n{passages_block}\n\n"
        "只输出 JSON：{\"verdict\": \"support\" | \"contradict\" | \"not_found\"}"
    )
    try:
        resp = cached_completion(
            client, model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=60,
            response_format={"type": "json_object"},
        )
        v = json.loads(resp.choices[0].message.content or "{}").get("verdict", "error")
        return v if v in {"support", "contradict", "not_found"} else "error"
    except Exception:
        return "error"


def run_hhard(
    rid: str, ers: list[dict], orig_text: str,
    searcher: HybridIndexSearcher,
    ds_client, qwen_client,
    ds_model: str, qwen_model: str,
    arm: str,
) -> list[dict]:
    """Run H_hard for all shalls of one source requirement."""
    rows = []
    for er in ers:
        shall = er.get("shall_statement", "").strip()
        if not shall:
            continue
        claims = extract_claims(shall, ds_client, ds_model)
        for claim in claims:
            passages = _kb_passages(searcher, claim, k=5)
            verdict  = _judge_claim_against_kb(claim, passages, qwen_client, qwen_model)
            oi       = judge_over_inference(shall, orig_text, passages,
                                            qwen_client, qwen_model, arm=arm)
            rows.append({
                "source_requirement_id": rid,
                "shall_snippet": shall[:120],
                "shall_full": shall,
                "retrieved_passages": passages,
                "evaluation_version": "claim-verdict-v2-errors-explicit",
                "claim": claim,
                "verdict": verdict,
                "over_inference": oi,
                "_arm": arm,
            })
            time.sleep(0.1)
    return rows


def _shalls_text(ers: list[dict]) -> str:
    return "\n".join(f"- {er.get('shall_statement','')}" for er in ers if er.get("shall_statement"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-hhard", action="store_true", help="只跑盲评，跳过 H_hard")
    ap.add_argument("--rag-file",   default=str(EXP / "rag_v3_results.json"),
                    help="RAG 结果文件路径")
    ap.add_argument("--norag-file", default=str(EXP / "norag_results.json"),
                    help="no-RAG 结果文件路径")
    ap.add_argument("--out-dir",    default=str(EXP),
                    help="输出目录（eval_v3.json / eval_v3_summary.txt 写入此处）")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = get_config()
    if not cfg.deepseek.enabled or not cfg.qwen.enabled:
        sys.exit("需要 DeepSeek + Qwen API key")
    ds_client   = cfg.deepseek.make_client();  ds_model   = cfg.deepseek.model
    qwen_client = cfg.qwen.make_client();       qwen_model = cfg.qwen.model

    rag, norag = _load_results(Path(args.rag_file), Path(args.norag_file))
    orig       = _load_orig()
    rids = sorted(set(rag) & set(norag) & set(orig))
    if args.limit:
        rids = rids[:args.limit]
    print(f"评估 {len(rids)} 条配对需求")

    # ── 索引（H_hard 用）────────────────────────────────────────────────────
    if not args.skip_hhard:
        print("加载索引…")
        from cooling_rag_mg.index_store import HybridIndexSearcher, load_index
        idx      = load_index(IDX)
        searcher = HybridIndexSearcher(idx, device="cpu")

    # ── 主循环 ───────────────────────────────────────────────────────────────
    hhard_rows: list[dict] = []        # per-claim 行
    quality_rows: list[dict] = []      # per-source 配对盲评

    for i, rid in enumerate(rids, 1):
        orig_text  = orig[rid]
        rag_ers    = rag[rid].get("engineering_requirements", [])
        norag_ers  = norag[rid].get("engineering_requirements", [])
        print(f"\n[{i:2d}/{len(rids)}] {rid}: {orig_text[:45]}…")

        # H_hard
        if not args.skip_hhard:
            print("  H_hard RAG v3…")
            hhard_rows += run_hhard(rid, rag_ers, orig_text,
                                    searcher, ds_client, qwen_client,
                                    ds_model, qwen_model, arm="rag")
            print("  H_hard no-RAG…")
            hhard_rows += run_hhard(rid, norag_ers, orig_text,
                                    searcher, ds_client, qwen_client,
                                    ds_model, qwen_model, arm="no-rag")

        # 盲评（RAG = R，no-RAG = B0）
        print("  盲评…")
        r_text  = _shalls_text(rag_ers)
        b0_text = _shalls_text(norag_ers)
        cons, biased = consensus_pair(
            orig_text, r_text=r_text, b0_text=b0_text,
            client=qwen_client, model=qwen_model,
        )
        row = {"source_requirement_id": rid}
        row.update({f"blind_{k}": v for k, v in cons.items()})
        row.update({f"bias_{k}": biased.get(k, False) for k in cons})
        quality_rows.append(row)
        print(f"  盲评结果: {cons}")

    # ── 聚合 ────────────────────────────────────────────────────────────────
    # H_hard：按源需求聚合，配对比较
    rag_src_stats:   dict[str, dict] = {}
    norag_src_stats: dict[str, dict] = {}
    if not args.skip_hhard:
        for arm_label, store in [("rag", rag_src_stats), ("no-rag", norag_src_stats)]:
            arm_rows = [r for r in hhard_rows if r["_arm"] == arm_label]
            for rid in rids:
                src_rows = [r for r in arm_rows if r["source_requirement_id"] == rid]
                if not src_rows:
                    continue
                verdicts = [r["verdict"] for r in src_rows]
                n_total = len(verdicts)
                n = sum(v in {"support", "contradict", "not_found"} for v in verdicts)
                oi_vals = [r["over_inference"] for r in src_rows if r["over_inference"] is not None]
                store[rid] = {
                    "n_claims": n_total,
                    "evaluated_claim_denominator": n,
                    "n_errors": verdicts.count("error"),
                    "h_hard":     verdicts.count("contradict") / n if n else None,
                    "h_soft":     verdicts.count("not_found")  / n if n else None,
                    "oi_rate":    sum(oi_vals) / len(oi_vals)  if oi_vals else None,
                    "verdict_dist": dict(Counter(verdicts)),
                }

    # 盲评聚合
    blind_agg = aggregate_quality(
        [{d: r[f"blind_{d}"] for d in DIMS} for r in quality_rows]
    )

    # ── 统计检验（H_hard 配对 Wilcoxon）────────────────────────────────────
    wilcoxon_result = {}
    if not args.skip_hhard and rag_src_stats and norag_src_stats:
        from scipy import stats as sp
        paired_rids = [rid for rid in rids
                       if rag_src_stats.get(rid, {}).get("h_hard") is not None
                       and norag_src_stats.get(rid, {}).get("h_hard") is not None]
        rag_hhard   = [rag_src_stats[r]["h_hard"]   for r in paired_rids]
        norag_hhard = [norag_src_stats[r]["h_hard"] for r in paired_rids]
        if len(paired_rids) >= 5:
            stat, p = sp.wilcoxon(rag_hhard, norag_hhard, zero_method="wilcox")
            wilcoxon_result = {
                "n_pairs": len(paired_rids),
                "rag_mean":   sum(rag_hhard)   / len(rag_hhard),
                "norag_mean": sum(norag_hhard) / len(norag_hhard),
                "statistic": float(stat), "p_value": float(p),
            }

    # ── 写出 ────────────────────────────────────────────────────────────────
    result = {
        "evaluation_version": "claim-verdict-v2-errors-explicit",
        "unit": "claims extracted from shall_statement only; criterion excluded; error excluded from evaluated denominator",
        "h_hard": {
            "rag_v3":  rag_src_stats,
            "no_rag":  norag_src_stats,
            "wilcoxon": wilcoxon_result,
            "per_claim_rows": hhard_rows,
        },
        "blind_quality": {
            "per_source": quality_rows,
            "aggregate":  blind_agg,
        },
        "descriptive": {
            "rag_v3": {
                "n_sources": len(rids),
                "n_shalls":  sum(len(rag[r].get("engineering_requirements",[])) for r in rids),
                "numeric_fraction": sum(
                    1 for r in rids for er in rag[r].get("engineering_requirements",[])
                    if _NUM_RE.search(er.get("shall_statement",""))
                ) / max(1, sum(len(rag[r].get("engineering_requirements",[])) for r in rids)),
                "attribution_rate": sum(
                    1 for r in rids for er in rag[r].get("engineering_requirements",[])
                    if _has_attribution(er)
                ) / max(1, sum(len(rag[r].get("engineering_requirements",[])) for r in rids)),
            },
            "no_rag": {
                "n_sources": len(rids),
                "n_shalls":  sum(len(norag[r].get("engineering_requirements",[])) for r in rids),
                "numeric_fraction": sum(
                    1 for r in rids for er in norag[r].get("engineering_requirements",[])
                    if _NUM_RE.search(er.get("shall_statement",""))
                ) / max(1, sum(len(norag[r].get("engineering_requirements",[])) for r in rids)),
                "attribution_rate": 0.0,
            },
        },
    }

    out_json = out_dir / "eval_v3.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 可读摘要
    _write_summary(result, out_dir / "eval_v3_summary.txt", args.skip_hhard)
    print(f"\n结果写入: {out_json}")
    print(f"摘要写入: {out_dir / 'eval_v3_summary.txt'}")


def _write_summary(result: dict, path: Path, skip_hhard: bool) -> None:
    lines = ["=" * 60, "v3 实验评估摘要", "=" * 60, ""]

    # 描述统计
    desc = result["descriptive"]
    lines += [
        "【描述统计】",
        f"  RAG v3:  {desc['rag_v3']['n_shalls']} shall / {desc['rag_v3']['n_sources']} 源  "
        f"数字含量 {desc['rag_v3']['numeric_fraction']:.1%}  "
        f"有归因 {desc['rag_v3']['attribution_rate']:.1%}",
        f"  no-RAG:  {desc['no_rag']['n_shalls']} shall / {desc['no_rag']['n_sources']} 源  "
        f"数字含量 {desc['no_rag']['numeric_fraction']:.1%}  "
        f"有归因 {desc['no_rag']['attribution_rate']:.1%}",
        "",
    ]

    # H_hard
    if not skip_hhard:
        wx = result["h_hard"].get("wilcoxon", {})
        lines += [
            "【H_hard 矛盾率（主要可靠性指标）】",
            f"  RAG v3  均值: {wx.get('rag_mean',0):.4f}",
            f"  no-RAG  均值: {wx.get('norag_mean',0):.4f}",
            f"  配对 Wilcoxon: n={wx.get('n_pairs','?')}, "
            f"p={wx.get('p_value',float('nan')):.4f}",
            "",
        ]

    # 盲评
    agg = result["blind_quality"]["aggregate"]
    lines += ["【4维盲评（RAG v3 vs no-RAG）】"]
    for dim in ["completeness", "actionability", "consistency", "verifiability"]:
        d = agg.get(dim, {})
        lines.append(
            f"  {dim:<14s}: R(RAG v3)={d.get('R',0):3d}  "
            f"tie={d.get('tie',0):3d}  B0(no-RAG)={d.get('B0',0):3d}"
        )
    ov = agg.get("overall", {})
    lines += [
        f"  overall       : R(RAG v3)={ov.get('R',0):3d}  "
        f"tie={ov.get('tie',0):3d}  B0(no-RAG)={ov.get('B0',0):3d}",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    for l in lines:
        print(l)


if __name__ == "__main__":
    main()
