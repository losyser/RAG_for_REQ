# scripts/46_evaluate_v2.py
# -*- coding: utf-8 -*-
"""Phase v2 Task 7：评估 no-RAG vs RAG 两产线。

三支柱（生成者=DeepSeek，裁判一律用与生成者不同的厂商，破自评偏袒）：
1) 可靠性（KB 锚点，复用 credibility_eval，**裁判=Qwen**）：每条 shall → DeepSeek 抽 claim →
   evidence_units 索引回溯 → Qwen 判 support/contradict/not_found；**矛盾率 H_hard 为主**、
   查无率 H_soft 只描述；Qwen 判过推断 OI。按源需求聚合，配对 Wilcoxon + bootstrap CI。
2) 质量盲评（quality_judge，裁判=Qwen）：每源把 no-RAG 全部 shall 拼 b0_text、RAG 拼 r_text，
   双跑左右交换取共识（不一致→tie 并记位置偏置），汇总各维 R/B0/tie + 总体胜负。
   引用/可溯源**不进**质量维度（否则天然偏 RAG）。
3) 描述统计：可溯源率、含数字占比、篇幅、覆盖证据数。
质量盲评抽样导出 CSV 供人工背书。

用法：
  python scripts/46_evaluate_v2.py --limit 3     # 冒烟（先看花费规模）
  python scripts/46_evaluate_v2.py               # 全量
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.credibility_eval import (
    aggregate_by_source, extract_claims, judge_claim_llm, judge_over_inference, metric_map,
)
from cooling_rag_mg.grounding import paired_compare
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.quality_eval import (
    aggregate_quality, consensus_pair, numeric_fraction, traceability_rate,
)
from cooling_rag_mg.quality_judge import DIMS


def _make_kb_search(cfg):
    """evidence_units 索引语义+BM25 检索，claim->段落文本列表（与 scripts/43 同一把尺子）。"""
    from cooling_rag_mg.hybrid_fusion import rrf_fuse
    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index
    searcher = HybridIndexSearcher(load_index(str(cfg.paths.indexes_dir / "evidence_units")),
                                   device=cfg.model.device)

    def kb_search(query: str, k: int) -> list[str]:
        vec = searcher.vector_search(query, k * 3)
        bm = searcher.bm25_search(query, k * 3)
        return [c.get("text", "") for c in rrf_fuse([vec, bm])[:k] if c.get("text")]
    return kb_search


def _shalls(rs):
    return [str(er.get("shall_statement", "")).strip()
            for er in (rs.get("engineering_requirements") or []) if str(er.get("shall_statement", "")).strip()]


def _eval_reliability(arm, sets, orig_map, kb_search, ds, ds_model, judge, judge_model,
                      top_k, all_calib, vc):
    rows = []
    for rs in sets:
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
                vc[v] += 1
                all_calib.append({"arm": arm, "source": src, "claim": c,
                                  "verdict_auto": v, "passages": " || ".join(passages[:3])})
            n = len(claims)
            oi = judge_over_inference(shall, src_text, kb_search(shall, top_k), judge, judge_model)
            rows.append({"source_requirement_id": src,
                         "h_hard": verds.count("contradict") / n if n else None,
                         "h_soft": verds.count("not_found") / n if n else None,
                         "over_inference": oi, "n_claims": n})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-dir", default=None, help="含 norag/rag_results.json 的目录（缺省 exp_v2）")
    ap.add_argument("--limit", type=int, default=0, help="每组只评前 N 个源需求（0=全量）")
    ap.add_argument("--top-k", type=int, default=8, help="KB 回溯 top_k")
    ap.add_argument("--calib-n", type=int, default=40, help="质量盲评人工校准抽样对数")
    args = ap.parse_args()

    cfg = get_config()
    if not (cfg.deepseek.enabled and cfg.qwen.enabled):
        print("需 DeepSeek(抽取) + Qwen(裁判) 两个 API key（.env）。"); sys.exit(1)

    exp_dir = Path(args.exp_dir) if args.exp_dir else cfg.paths.search_results_dir / "exp_v2"
    norag = json.loads((exp_dir / "norag_results.json").read_text(encoding="utf-8"))["result_sets"]
    rag = json.loads((exp_dir / "rag_results.json").read_text(encoding="utf-8"))["result_sets"]
    if args.limit:
        norag, rag = norag[: args.limit], rag[: args.limit]

    orig_map = {x["requirement_id"]: x.get("requirement_text", "")
                for x in read_jsonl(cfg.paths.processed_dir / "original_requirements_v1.jsonl")}
    rag_by_src = {rs.get("source_requirement_id", ""): rs for rs in rag}

    kb_search = _make_kb_search(cfg)
    ds = cfg.deepseek.make_client()
    judge = cfg.qwen.make_client()
    print(f"[eval-v2] no-RAG={len(norag)} RAG={len(rag)} 源；抽取=DeepSeek 裁判=Qwen top_k={args.top_k}")

    random.seed(42)

    # ── 支柱 1：可靠性 ──
    all_calib_rel, vc = [], Counter()
    rel = {"arms": {}, "comparisons": {}, "config": {"top_k": args.top_k}}
    aggs = {}
    for arm, sets in [("no-RAG", norag), ("RAG", rag)]:
        rows = _eval_reliability(arm, sets, orig_map, kb_search, ds, cfg.deepseek.model,
                                 judge, cfg.qwen.model, args.top_k, all_calib_rel, vc)
        agg = aggregate_by_source(rows)
        aggs[arm] = agg

        def _m(metric, a=agg):
            vals = [d[metric] for d in a.values() if d.get(metric) is not None]
            return sum(vals) / len(vals) if vals else float("nan")
        rel["arms"][arm] = {"n_sources": len(agg),
                            "n_shalls": sum(d["n_shalls"] for d in agg.values()),
                            "h_hard": _m("h_hard_mean"), "h_soft": _m("h_soft_mean"),
                            "oi_rate": _m("oi_rate")}
        print(f"  [{arm}] sources={len(agg)} H_hard={_m('h_hard_mean'):.3f} "
              f"H_soft={_m('h_soft_mean'):.3f} OI={_m('oi_rate'):.3f}")
    for metric, key in [("H_hard", "h_hard_mean"), ("H_soft", "h_soft_mean"), ("OI", "oi_rate")]:
        # 配对方向：a=no-RAG b=RAG，diff=no-RAG−RAG，正值=RAG 更低（更好）
        cmp = paired_compare(metric_map(aggs["no-RAG"], key), metric_map(aggs["RAG"], key))
        rel["comparisons"][metric] = cmp
        print(f"  [{metric}] no-RAG={cmp['mean_a']:.3f} RAG={cmp['mean_b']:.3f} "
              f"diff(noRAG-RAG)={cmp['mean_diff']:+.3f} p={cmp['pvalue']:.3f} "
              f"CI[{cmp['ci_low']:+.3f},{cmp['ci_high']:+.3f}] n={cmp['n_pairs']}")
    rel["verdict_distribution"] = dict(vc)

    # ── 支柱 2：质量盲评（共识 + 位置偏置） ──
    qrows, bias_counter, quality_calib = [], Counter(), []
    paired_srcs = [rs.get("source_requirement_id", "") for rs in norag
                   if rs.get("source_requirement_id", "") in rag_by_src]
    for src in paired_srcs:
        norag_rs = next(rs for rs in norag if rs.get("source_requirement_id", "") == src)
        b0_text = "\n".join(f"- {s}" for s in _shalls(norag_rs))
        r_text = "\n".join(f"- {s}" for s in _shalls(rag_by_src[src]))
        if not b0_text.strip() or not r_text.strip():
            continue
        req = orig_map.get(src, "")
        cons, biased = consensus_pair(req, r_text=r_text, b0_text=b0_text,
                                      client=judge, model=cfg.qwen.model)
        qrows.append(cons)
        for d in DIMS:
            if biased[d]:
                bias_counter[d] += 1
        quality_calib.append({"source": src, "requirement": req,
                              "norag_shalls": b0_text, "rag_shalls": r_text,
                              **{f"auto_{d}": cons[d] for d in DIMS}})
    qagg = aggregate_quality(qrows)
    quality = {"n_pairs": len(qrows), "dimensions": qagg,
               "position_bias_count": dict(bias_counter)}
    print(f"  [质量] 配对={len(qrows)} 总体 R/B0/tie="
          f"{qagg['overall']['R']}/{qagg['overall']['B0']}/{qagg['overall']['tie']}"
          f"  位置偏置(降为tie)={dict(bias_counter)}")
    for d in DIMS:
        print(f"     {d}: R{qagg[d]['R']} B0{qagg[d]['B0']} tie{qagg[d]['tie']}")

    # ── 支柱 3：描述统计 ──
    desc = {}
    for arm, sets in [("no-RAG", norag), ("RAG", rag)]:
        all_ers = [er for rs in sets for er in (rs.get("engineering_requirements") or [])]
        shall_lens = [len(str(er.get("shall_statement", ""))) for er in all_ers
                      if str(er.get("shall_statement", "")).strip()]
        desc[arm] = {
            "n_shalls": len(shall_lens),
            "traceability_rate": traceability_rate(all_ers),
            "numeric_fraction": numeric_fraction(all_ers),
            "avg_shall_len": sum(shall_lens) / len(shall_lens) if shall_lens else 0.0,
            "avg_shalls_per_source": len(shall_lens) / len(sets) if sets else 0.0,
        }
    print(f"  [描述] no-RAG {desc['no-RAG']}  |  RAG {desc['RAG']}")

    # ── 落盘 ──
    out = {"reliability": rel, "quality": quality, "descriptive": desc}
    out_json = cfg.paths.search_results_dir / "exp_v2" / "eval_v2.json"
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # 可靠性人工校准（分层：先收全部 contradict，再均衡填 not_found/support）
    groups = defaultdict(list)
    for row in all_calib_rel:
        groups[(row["arm"], row["verdict_auto"])].append(row)
    for g in groups.values():
        random.shuffle(g)
    calib = list(groups.get(("no-RAG", "contradict"), [])) + list(groups.get(("RAG", "contradict"), []))
    cells = [("no-RAG", "not_found"), ("RAG", "not_found"), ("no-RAG", "support"), ("RAG", "support")]
    i = 0
    while len(calib) < 50 and any(groups[c] for c in cells):
        c = cells[i % len(cells)]; i += 1
        if groups[c]:
            calib.append(groups[c].pop())
    rel_csv = cfg.paths.search_results_dir / "exp_v2" / "reliability_calibration_v2.csv"
    with rel_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arm", "source", "claim", "verdict_auto",
                                          "verdict_human", "claim_reasonable", "passages"])
        w.writeheader()
        for row in calib[:50]:
            row["verdict_human"] = ""; row["claim_reasonable"] = ""
            w.writerow(row)

    # 质量盲评人工校准抽样
    random.shuffle(quality_calib)
    qcalib = quality_calib[: args.calib_n]
    q_csv = cfg.paths.search_results_dir / "exp_v2" / "quality_calibration_v2.csv"
    with q_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["source", "requirement", "norag_shalls", "rag_shalls"] + \
                 [f"auto_{d}" for d in DIMS] + [f"human_{d}" for d in DIMS]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in qcalib:
            for d in DIMS:
                row[f"human_{d}"] = ""
            w.writerow(row)

    print(f"verdict 分布: {dict(vc)}")
    print(f"-> {out_json}\n-> {rel_csv}（{len(calib[:50])} 条）\n-> {q_csv}（{len(qcalib)} 对）")


if __name__ == "__main__":
    main()
