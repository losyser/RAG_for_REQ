# scripts/43_credibility_eval.py
# -*- coding: utf-8 -*-
"""Phase 2 Task 2.6：对 B0/R 跑公平可信度评估层。

对每条 shall：DeepSeek 抽 claim → 各 claim 拿 KB 回溯(evidence_units 索引)→ ERNIE 判
support/contradict/not_found；硬幻觉 H_hard=contradict、软幻觉 H_soft=not_found；
ERNIE 再判过推断 OI。按源需求聚合，B0 vs R 配对 Wilcoxon。

跨厂商：生成=Qwen，抽取=DeepSeek，裁判=ERNIE（均与生成者不同），破自评偏袒。
两组用同一 kb_search+judge，破 M1 循环。导出人工校准抽样供背书。

用法：
  python scripts/43_credibility_eval.py --limit 3        # 冒烟
  python scripts/43_credibility_eval.py                  # 全量
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.credibility_eval import (
    aggregate_by_source, extract_claims, judge_claim_llm, judge_over_inference,
    metric_map,
)
from cooling_rag_mg.grounding import paired_compare
from cooling_rag_mg.jsonl import read_jsonl


def _make_kb_search(cfg):
    """基于 evidence_units 索引的语义+BM25 检索，返回 claim->段落文本列表。大 top_k 兜底软幻觉。"""
    from cooling_rag_mg.hybrid_fusion import rrf_fuse
    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index
    searcher = HybridIndexSearcher(load_index(str(cfg.paths.indexes_dir / "evidence_units")),
                                   device=cfg.model.device)

    def kb_search(query: str, k: int) -> list[str]:
        vec = searcher.vector_search(query, k * 3)
        bm = searcher.bm25_search(query, k * 3)
        fused = rrf_fuse([vec, bm])[:k]
        return [c.get("text", "") for c in fused if c.get("text")]
    return kb_search


def _eval_arm(arm, result_sets, orig_map, kb_search, ds, ds_model, judge, judge_model,
              top_k, calib, calib_n, verdicts_counter):
    rows = []
    for rs in result_sets:
        src = rs.get("source_requirement_id", "")
        src_text = orig_map.get(src, "")
        for er in rs.get("engineering_requirements", []) or []:
            shall = str(er.get("shall_statement", "")).strip()
            if not shall:
                continue
            claims = extract_claims(shall, ds, ds_model)
            verds = []
            for c in claims:
                passages = kb_search(c, top_k)
                v = judge_claim_llm(c, passages, judge, judge_model) if passages else "not_found"
                verds.append(v)
                verdicts_counter[v] += 1
                if len(calib) < calib_n:
                    calib.append({"arm": arm, "source": src, "claim": c,
                                  "verdict_auto": v, "passages": " || ".join(passages[:3])})
            n = len(claims)
            h_hard = verds.count("contradict") / n if n else None
            h_soft = verds.count("not_found") / n if n else None
            oi = judge_over_inference(shall, src_text, kb_search(shall, top_k), judge, judge_model)
            rows.append({"source_requirement_id": src, "h_hard": h_hard,
                         "h_soft": h_soft, "over_inference": oi, "n_claims": n})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-dir", default=None, help="含 B0/R_results.json 的目录（缺省 main_experiment）")
    ap.add_argument("--limit", type=int, default=0, help="每组只评前 N 个源需求（0=全量）")
    ap.add_argument("--top-k", type=int, default=8, help="KB 回溯 top_k（大些兜底软幻觉）")
    ap.add_argument("--calib-n", type=int, default=50, help="人工校准抽样条数")
    args = ap.parse_args()

    cfg = get_config()
    if not (cfg.deepseek.enabled and cfg.ernie.enabled):
        print("需 DeepSeek(抽取) + ERNIE(裁判) 两个 API key（.env）。"); sys.exit(1)

    exp_dir = Path(args.exp_dir) if args.exp_dir else cfg.paths.search_results_dir / "main_experiment"
    b0 = json.loads((exp_dir / "B0_results.json").read_text(encoding="utf-8"))["result_sets"]
    r = json.loads((exp_dir / "R_results.json").read_text(encoding="utf-8"))["result_sets"]
    if args.limit:
        b0, r = b0[: args.limit], r[: args.limit]

    orig_map = {x["requirement_id"]: x.get("requirement_text", "")
                for x in read_jsonl(cfg.paths.processed_dir / "original_requirements_v1.jsonl")}
    kb_search = _make_kb_search(cfg)
    ds = cfg.deepseek.make_client()
    judge = cfg.ernie.make_client()
    print(f"[eval] B0={len(b0)} R={len(r)} 源需求；抽取=DeepSeek 裁判=ERNIE top_k={args.top_k}")

    random.seed(42)
    calib: list[dict] = []
    vc = Counter()
    out = {"arms": {}, "comparisons": {}, "config": {"top_k": args.top_k}}
    aggs = {}
    for arm, sets in [("B0", b0), ("R", r)]:
        rows = _eval_arm(arm, sets, orig_map, kb_search, ds, cfg.deepseek.model,
                         judge, cfg.ernie.model, args.top_k, calib, args.calib_n, vc)
        agg = aggregate_by_source(rows)
        aggs[arm] = agg

        def _m(metric):
            vals = [d[metric] for d in agg.values() if d.get(metric) is not None]
            return sum(vals) / len(vals) if vals else float("nan")
        out["arms"][arm] = {"n_sources": len(agg), "n_shalls": sum(d["n_shalls"] for d in agg.values()),
                            "h_hard": _m("h_hard_mean"), "h_soft": _m("h_soft_mean"),
                            "oi_rate": _m("oi_rate")}
        print(f"  [{arm}] sources={len(agg)} H_hard={_m('h_hard_mean'):.3f} "
              f"H_soft={_m('h_soft_mean'):.3f} OI={_m('oi_rate'):.3f}")

    for metric, key in [("H_hard", "h_hard_mean"), ("H_soft", "h_soft_mean"), ("OI", "oi_rate")]:
        cmp = paired_compare(metric_map(aggs["B0"], key), metric_map(aggs["R"], key))
        out["comparisons"][metric] = cmp
        print(f"  [{metric}] B0={cmp['mean_a']:.3f} R={cmp['mean_b']:.3f} "
              f"diff(B0-R)={cmp['mean_diff']:+.3f} p={cmp['pvalue']:.3f} "
              f"CI[{cmp['ci_low']:+.3f},{cmp['ci_high']:+.3f}] n={cmp['n_pairs']}")

    out["verdict_distribution"] = dict(vc)
    out_json = cfg.paths.search_results_dir / "credibility_eval.json"
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    calib_csv = cfg.paths.search_results_dir / "credibility_calibration_sample.csv"
    with calib_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arm", "source", "claim", "verdict_auto", "verdict_human", "passages"])
        w.writeheader()
        for row in calib:
            row["verdict_human"] = ""
            w.writerow(row)
    print(f"verdict 分布: {dict(vc)}")
    print(f"-> {out_json}\n-> {calib_csv}（{len(calib)} 条待人工校准）")


if __name__ == "__main__":
    main()
