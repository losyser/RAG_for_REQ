# scripts/75_ablation_retrieval.py
"""
消融实验：检索策略对比
4个臂，固定生成端(generate_rag_v3)，只变检索端：

  filtered_rrf  : analyze_requirement → filtered BM25+vec+RRF  (v3基线，直接复用已有结果)
  nofilter_rrf  : 无元数据过滤，全量BM25+vec+RRF
  filtered_bm25 : analyze_requirement → filtered BM25-only
  filtered_vec  : analyze_requirement → filtered vector-only

输出:
  data/search_results/ablation/nofilter_rrf_results.json
  data/search_results/ablation/filtered_bm25_results.json
  data/search_results/ablation/filtered_vec_results.json
  (filtered_rrf 直接复用 exp_v3/rag_v3_results.json，不重新生成)

用法:
  python scripts/75_ablation_retrieval.py --limit 5   # 冒烟
  python scripts/75_ablation_retrieval.py             # 全量
  python scripts/75_ablation_retrieval.py --arms nofilter_rrf filtered_bm25  # 指定臂
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.hybrid_fusion import rrf_fuse
from cooling_rag_mg.index_store import HybridIndexSearcher, load_index
from cooling_rag_mg.req_generation_v2 import generate_rag_v3
from cooling_rag_mg.requirement_analyzer import analyze_requirement

DATA     = PROJECT_ROOT / "data"
REQ_PATH = DATA / "processed" / "original_requirements_v2.jsonl"
OUT_DIR  = DATA / "search_results" / "ablation"
IDX_DIR  = DATA / "indexes" / "evidence_units"

ALL_ARMS = ["nofilter_rrf", "filtered_bm25", "filtered_vec"]


# ── 各臂检索函数 ──────────────────────────────────────────────────────────────

def retrieve_nofilter_rrf(
    req_text: str,
    searcher: HybridIndexSearcher,
    *,
    per_k: int = 20,
    max_total: int = 30,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """无元数据过滤：全量BM25+向量+RRF。"""
    vec = searcher.vector_search(req_text, per_k)
    bm  = searcher.bm25_search(req_text, per_k)
    seen: dict[str, dict] = {}
    for cand in rrf_fuse([vec, bm]):
        cid = cand.get("id") or cand.get("chunk_id")
        if cid and cid not in seen:
            seen[cid] = cand
        if len(seen) >= max_total:
            break
    return list(seen.values()), []   # pairs=[] 表示无过滤


def retrieve_filtered_bm25(
    req_text: str,
    pairs: list[tuple[str, str]],
    searcher: HybridIndexSearcher,
    *,
    per_pair_k: int = 8,
    max_total: int = 30,
    fallback_k: int = 15,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """有元数据过滤，仅BM25（无向量）。"""
    if not pairs:
        bm = searcher.bm25_search(req_text, fallback_k)
        seen = {(r.get("id") or r.get("chunk_id")): r for r in bm if r.get("id") or r.get("chunk_id")}
        return list(seen.values()), []

    seen: dict[str, dict] = {}
    for comp, intent in pairs:
        results = searcher.filtered_bm25_search(
            req_text, per_pair_k, components=[comp], intents=[intent]
        )
        for cand in results:
            cid = cand.get("id") or cand.get("chunk_id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                return list(seen.values()), pairs
    return list(seen.values()), pairs


def retrieve_filtered_vec(
    req_text: str,
    pairs: list[tuple[str, str]],
    searcher: HybridIndexSearcher,
    *,
    per_pair_k: int = 8,
    max_total: int = 30,
    fallback_k: int = 15,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """有元数据过滤，仅向量（无BM25）。"""
    if not pairs:
        vec = searcher.vector_search(req_text, fallback_k)
        seen = {(r.get("id") or r.get("chunk_id")): r for r in vec if r.get("id") or r.get("chunk_id")}
        return list(seen.values()), []

    seen: dict[str, dict] = {}
    for comp, intent in pairs:
        results = searcher.filtered_vector_search(
            req_text, per_pair_k, components=[comp], intents=[intent]
        )
        for cand in results:
            cid = cand.get("id") or cand.get("chunk_id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                return list(seen.values()), pairs
    return list(seen.values()), pairs


# ── 运行单个臂 ────────────────────────────────────────────────────────────────

def run_arm(
    arm_name: str,
    reqs: list[dict],
    searcher: HybridIndexSearcher,
    ds_client: Any,
    ds_model: str,
) -> list[dict]:
    print(f"\n{'='*55}")
    print(f"臂: {arm_name}  ({len(reqs)} 条需求)")
    print(f"{'='*55}")

    results: list[dict] = []
    n_breaker = 0

    for i, req in enumerate(reqs, 1):
        rid        = req.get("requirement_id", f"R{i:03d}")
        text       = req.get("requirement_text", "")
        stakeholder = req.get("stakeholder", "")
        print(f"\n[{i:2d}/{len(reqs)}] {rid}: {text[:50]}...")

        # 第一步：分析需求，抽 (component,intent) 对（nofilter_rrf 不需要此步）
        if arm_name == "nofilter_rrf":
            pairs: list[tuple[str, str]] = []
        else:
            pairs = analyze_requirement(text, ds_client, ds_model)
            print(f"  analyze: {len(pairs)} 对 → {[f'{c}×{i2}' for c, i2 in pairs]}")

        # 第二步：检索
        if arm_name == "nofilter_rrf":
            evidence_list, pairs_used = retrieve_nofilter_rrf(text, searcher)
        elif arm_name == "filtered_bm25":
            evidence_list, pairs_used = retrieve_filtered_bm25(text, pairs, searcher)
        elif arm_name == "filtered_vec":
            evidence_list, pairs_used = retrieve_filtered_vec(text, pairs, searcher)
        else:
            raise ValueError(f"未知臂: {arm_name}")

        print(f"  检索: {len(evidence_list)} 条证据 (pairs_used={len(pairs_used)})")

        # 第三步：生成
        ers = generate_rag_v3(text, evidence_list, ds_client, ds_model)

        if not ers:
            n_breaker += 1
            print(f"  [!] RAG 返回空（连续 {n_breaker} 次）")
            if n_breaker >= 5:
                sys.exit("熔断：连续5次空结果，检查 API")
        else:
            n_breaker = 0
            n_with_ev = sum(1 for er in ers if er.get("evidence_ids"))
            print(f"  生成: {len(ers)} shall，{n_with_ev}/{len(ers)} 有归因")

        results.append({
            "source_requirement_id": rid,
            "stakeholder":           stakeholder,
            "_arm":                  arm_name,
            "_pairs_used":           [f"{c}×{i2}" for c, i2 in pairs_used],
            "_n_evidence":           len(evidence_list),
            "_n_pairs":              len(pairs_used),
            "engineering_requirements": ers,
        })
        time.sleep(0.2)

    # 汇总
    total_shall = sum(len(r["engineering_requirements"]) for r in results)
    total_ev    = sum(1 for r in results for er in r["engineering_requirements"] if er.get("evidence_ids"))
    print(f"\n{arm_name}: {len(results)} 源 / {total_shall} shall / 有归因 {total_ev}/{total_shall}")
    return results


def _save(path: Path, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"已写入: {path}")


# ── 主函数 ────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前N条需求（冒烟）")
    ap.add_argument("--arms", nargs="+", choices=ALL_ARMS, default=ALL_ARMS,
                    help="指定要运行的臂（默认全部）")
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    ds_client = cfg.deepseek.make_client()
    ds_model  = cfg.deepseek.model

    print("加载索引...")
    idx     = load_index(IDX_DIR)
    device  = cfg.device if hasattr(cfg, "device") else "cpu"
    searcher = HybridIndexSearcher(idx, device=device)

    with open(REQ_PATH, encoding="utf-8") as f:
        reqs = [json.loads(l) for l in f]
    if args.limit:
        reqs = reqs[:args.limit]
    print(f"需求: {len(reqs)} 条")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for arm in args.arms:
        results = run_arm(arm, reqs, searcher, ds_client, ds_model)
        _save(OUT_DIR / f"{arm}_results.json", {"arm": arm, "result_sets": results})

    print("\n全部完成。下一步：python scripts/76_ablation_verify.py")


if __name__ == "__main__":
    main()
