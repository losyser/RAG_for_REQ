# scripts/45_run_pipelines_v2.py
# -*- coding: utf-8 -*-
"""Phase v2 Task 6：跑 no-RAG 与 RAG 两条产线。

- no-RAG：DeepSeek 强基线据原始需求直接生成（不阉割）。
- RAG：Kimi 生成检索内容 → 覆盖优先检索(evidence_units) → DeepSeek 据证据生成。
两组终端均 DeepSeek。复用冻结 60 条原始需求。含熔断（连续空 no-RAG 即停）。

用法：
  python scripts/45_run_pipelines_v2.py --limit 2     # 冒烟
  python scripts/45_run_pipelines_v2.py               # 全量
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.coverage_retrieval import coverage_retrieve
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.req_generation_v2 import generate_norag, generate_rag
from cooling_rag_mg.retrieval_query_gen import generate_queries


def _result_set(arm, src_id, stake, ers, extra):
    return {"source_requirement_id": src_id, "stakeholder": stake, "_arm": arm,
            "engineering_requirements": ers, **extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--per-query-k", type=int, default=20)
    ap.add_argument("--max-total", type=int, default=30,
                    help="喂给生成的证据上限（覆盖优先但避免超大 prompt 超时/稀释）")
    args = ap.parse_args()

    cfg = get_config()
    if not (cfg.kimi.enabled and cfg.deepseek.enabled):
        print("需 Kimi + DeepSeek API key（.env）。"); sys.exit(1)

    sources = list(read_jsonl(cfg.paths.processed_dir / "original_requirements_v1.jsonl"))
    if args.limit:
        sources = sources[: args.limit]

    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index
    searcher = HybridIndexSearcher(load_index(str(cfg.paths.indexes_dir / "evidence_units")),
                                   device=cfg.model.device)
    kimi = cfg.kimi.make_client()
    ds = cfg.deepseek.make_client()
    print(f"[v2] {len(sources)} 源需求；no-RAG=DeepSeek 强基线，RAG=Kimi 检索内容→覆盖检索→DeepSeek")

    norag_sets, rag_sets = [], []
    consec_empty = 0
    cov_counts = []
    for i, src in enumerate(sources, start=1):
        sid = src.get("requirement_id") or src.get("source_requirement_id")
        stake = src.get("stakeholder", "")
        text = src.get("requirement_text", "")

        # ── no-RAG ──
        ne = generate_norag(text, ds, cfg.deepseek.model)
        norag_sets.append(_result_set("no-RAG", sid, stake, ne, {}))
        consec_empty = consec_empty + 1 if not ne else 0
        if consec_empty >= 5:
            print("\n[ABORT] 连续 5 个 no-RAG 为空——疑 API/计费故障，停止不保存残缺。"); sys.exit(2)

        # ── RAG ──
        queries = generate_queries(text, kimi, cfg.kimi.model, temperature=cfg.kimi.temperature)
        cands = coverage_retrieve(queries, searcher, per_query_k=args.per_query_k, max_total=args.max_total)
        ev_ids = [c.get("id") for c in cands if c.get("id")]
        ev_texts = [c.get("text", "") for c in cands if c.get("text")]
        cov_counts.append(len(cands))
        re = generate_rag(text, ev_texts, ev_ids, ds, cfg.deepseek.model)
        if not re and cands:  # 有证据却空 → 疑瞬时超时，重试一次
            re = generate_rag(text, ev_texts, ev_ids, ds, cfg.deepseek.model)
        rag_sets.append(_result_set("RAG", sid, stake, re,
                                    {"_n_queries": len(queries), "_n_evidence": len(cands)}))
        print(f"  [{i}/{len(sources)}] {sid}: no-RAG {len(ne)} ER | RAG {len(re)} ER "
              f"({len(queries)} 查询/{len(cands)} 证据)")

    out_dir = cfg.paths.search_results_dir / "exp_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "norag_results.json").write_text(
        json.dumps({"arm": "no-RAG", "result_sets": norag_sets}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "rag_results.json").write_text(
        json.dumps({"arm": "RAG", "result_sets": rag_sets}, ensure_ascii=False, indent=2), encoding="utf-8")
    avg_cov = sum(cov_counts) / len(cov_counts) if cov_counts else 0
    print(f"\nno-RAG: {sum(len(s['engineering_requirements']) for s in norag_sets)} ER")
    print(f"RAG   : {sum(len(s['engineering_requirements']) for s in rag_sets)} ER，平均检索证据 {avg_cov:.1f}/源")
    print(f"-> {out_dir}")


if __name__ == "__main__":
    main()
