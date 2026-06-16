# scripts/54_run_pipelines_v3.py
"""
v3 完整流程：对齐检索 + per-shall 证据归因。

与 v2 的核心区别：
  v2: Kimi宽泛查询 → coverage_retrieve → 30条无关证据 → 每条shall引用全部30个ID
  v3: requirement_analyzer → aligned_retrieve → 精准证据 → generate_rag_v3 → per-shall归因

产出：
  data/search_results/exp_v3/rag_v3_results.json   ← v3 RAG 结果
  data/search_results/exp_v3/norag_results.json    ← no-RAG 基线（复用v2，仅保留格式一致）

用法：
  python scripts/54_run_pipelines_v3.py --limit 5   # 冒烟
  python scripts/54_run_pipelines_v3.py             # 全量60条
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.coverage_retrieval import aligned_retrieve
from cooling_rag_mg.index_store import HybridIndexSearcher, load_index
from cooling_rag_mg.req_generation_v2 import generate_norag, generate_rag_v3

DATA     = PROJECT_ROOT / "data"
REQ_PATH = DATA / "processed" / "original_requirements_v2.jsonl"
OUT_DIR  = DATA / "search_results" / "exp_v3"


def _load_searcher(cfg) -> HybridIndexSearcher:
    idx_dir = DATA / "indexes" / "evidence_units"
    idx = load_index(idx_dir)
    device = cfg.device if hasattr(cfg, "device") else "cpu"
    return HybridIndexSearcher(idx, device=device)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    ds_client = cfg.deepseek.make_client()
    ds_model  = cfg.deepseek.model

    print("加载索引...")
    searcher = _load_searcher(cfg)

    with open(REQ_PATH, encoding="utf-8") as f:
        reqs = [json.loads(l) for l in f]
    if args.limit:
        reqs = reqs[:args.limit]
    print(f"处理 {len(reqs)} 条需求")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rag_results:   list[dict] = []
    norag_results: list[dict] = []

    n_breaker = 0   # 连续空 RAG 熔断计数
    for i, req in enumerate(reqs, 1):
        rid  = req.get("requirement_id", f"R{i:03d}")
        text = req.get("requirement_text", "")
        stakeholder = req.get("stakeholder", "")
        print(f"\n[{i:2d}/{len(reqs)}] {rid}: {text[:50]}...")

        # ── no-RAG 基线 ────────────────────────────────────────────────────
        norag_ers = generate_norag(text, ds_client, ds_model)
        norag_results.append({
            "source_requirement_id": rid,
            "stakeholder": stakeholder,
            "_arm": "no-rag",
            "engineering_requirements": norag_ers,
        })
        print(f"  no-RAG: {len(norag_ers)} shall")

        # ── v3 RAG：对齐检索 + per-shall 归因 ──────────────────────────────
        evidence_list, pairs_used = aligned_retrieve(
            text, searcher, ds_client, ds_model,
            per_pair_k=8, max_total=20,
        )
        print(f"  aligned_retrieve: {len(pairs_used)} 对 → {len(evidence_list)} 条证据")
        if pairs_used:
            for c, i2 in pairs_used:
                print(f"    ({c} × {i2})")

        rag_ers = generate_rag_v3(text, evidence_list, ds_client, ds_model)

        if not rag_ers:
            n_breaker += 1
            print(f"  ⚠ RAG 返回空（连续 {n_breaker} 次）")
            if n_breaker >= 5:
                sys.exit("熔断：连续5次 RAG 空结果，检查 API")
        else:
            n_breaker = 0

        # 统计 per-shall 归因质量
        n_with_evidence = sum(1 for er in rag_ers if er.get("evidence_ids"))
        avg_ev = (sum(len(er.get("evidence_ids", [])) for er in rag_ers) / len(rag_ers)
                  if rag_ers else 0)
        print(f"  RAG v3: {len(rag_ers)} shall，"
              f"{n_with_evidence}/{len(rag_ers)} 有证据归因，"
              f"平均 {avg_ev:.1f} 条/shall")

        rag_results.append({
            "source_requirement_id": rid,
            "stakeholder": stakeholder,
            "_arm": "rag-v3",
            "_pairs_used": [f"{c}×{i2}" for c, i2 in pairs_used],
            "_n_evidence": len(evidence_list),
            "_n_pairs":    len(pairs_used),
            "engineering_requirements": rag_ers,
        })

        time.sleep(0.2)

    # ── 落盘 ──────────────────────────────────────────────────────────────
    _save(OUT_DIR / "rag_v3_results.json",   {"arm": "rag-v3",  "result_sets": rag_results})
    _save(OUT_DIR / "norag_results.json",    {"arm": "no-rag",  "result_sets": norag_results})

    # ── 汇总 ──────────────────────────────────────────────────────────────
    total_rag  = sum(len(r["engineering_requirements"]) for r in rag_results)
    total_norag= sum(len(r["engineering_requirements"]) for r in norag_results)
    total_with_ev = sum(
        1 for r in rag_results
        for er in r["engineering_requirements"]
        if er.get("evidence_ids")
    )
    avg_pairs = (sum(r["_n_pairs"] for r in rag_results) / len(rag_results)
                 if rag_results else 0)
    avg_ev_per_src = (sum(r["_n_evidence"] for r in rag_results) / len(rag_results)
                      if rag_results else 0)

    print("\n" + "=" * 55)
    print("v3 流程完成")
    print("=" * 55)
    print(f"no-RAG: {len(norag_results)} 源 / {total_norag} shall")
    print(f"RAG v3: {len(rag_results)} 源 / {total_rag} shall")
    print(f"  有证据归因 shall: {total_with_ev}/{total_rag} "
          f"({total_with_ev/total_rag*100:.1f}%)" if total_rag else "")
    print(f"  平均检索对数/源: {avg_pairs:.1f}")
    print(f"  平均证据数/源:   {avg_ev_per_src:.1f}（v2 为 ~32）")
    print(f"结果目录: {OUT_DIR}")
    print("\n下一步评估：")
    print("  python scripts/46_evaluate_v2.py  （可复用评估脚本对比 v3 结果）")


def _save(path: Path, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"已写入: {path}")


if __name__ == "__main__":
    main()
