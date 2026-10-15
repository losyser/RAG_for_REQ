# scripts/101_stage1_baselines.py
"""E1：Stage 1（需求 → (c,i) 对）的 DeepSeek 结果与三种基线，并生成盲标候选池。
基线说明：
  bm25  —— 用 BM25 把需求文本与 183 个合法 (c,i) 的"部件描述+方面描述"做匹配，取 top-k
  embed —— BGE-M3 余弦相似度，取 top-k
  qwen  —— 同一个 analyzer prompt，换用 qwen-max
  k = 4，与 DeepSeek 平均每条需求约 3.8 个对的数量接近
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, all_pairs
from cooling_rag_mg.index_store import load_sentence_transformer
from cooling_rag_mg.requirement_analyzer import analyze_requirement
from cooling_rag_mg.text_utils import simple_tokens

E3 = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT = ROOT / "data/search_results/exp_v4"
K = 4


def pair_doc(c: str, i: str) -> str:
    return f"{c} {COMPONENTS.get(c, '')} {i} {INTENTS.get(i, '')}"


def main() -> None:
    cfg = get_config()
    reqs = [json.loads(l) for l in OR.open(encoding="utf-8")]
    pairs = all_pairs()
    docs = [pair_doc(c, i) for c, i in pairs]
    pred: dict[str, dict[str, list]] = {"deepseek": {}, "qwen": {}, "bm25": {}, "embed": {}}

    v3 = json.loads(E3.read_text(encoding="utf-8"))
    for rs in v3["result_sets"]:
        pred["deepseek"][rs["source_requirement_id"]] = [p.split("×") for p in rs.get("_pairs_used", [])]

    bm = BM25Okapi([simple_tokens(d) for d in docs])
    model = load_sentence_transformer(cfg.model.embedding_model_path, device=cfg.model.device, label="[E1]")
    dv = model.encode(docs, normalize_embeddings=True)
    qclient = cfg.qwen.make_client()
    for r in reqs:
        rid, text = r["requirement_id"], r["requirement_text"]
        s = bm.get_scores(simple_tokens(text))
        pred["bm25"][rid] = [list(pairs[j]) for j in np.argsort(s)[::-1][:K]]
        qv = model.encode([text], normalize_embeddings=True)[0]
        pred["embed"][rid] = [list(pairs[j]) for j in np.argsort(dv @ qv)[::-1][:K]]
        pred["qwen"][rid] = [list(p) for p in analyze_requirement(text, qclient, cfg.qwen.model)]
        print(rid, {k: len(v.get(rid, [])) for k, v in pred.items()}, flush=True)

    (OUT / "e1_predictions.json").write_text(json.dumps(pred, ensure_ascii=False, indent=1), encoding="utf-8")
    text_of = {r["requirement_id"]: r["requirement_text"] for r in reqs}
    pool = sorted({(rid, c, i) for sysd in pred.values() for rid, ps in sysd.items() for c, i in ps})
    random.Random(42).shuffle(pool)
    with (OUT / "e1_pool.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["or_id", "requirement_text", "component", "intent", "component_desc", "intent_desc"])
        for rid, c, i in pool:
            w.writerow([rid, text_of[rid], c, i, COMPONENTS.get(c, ""), INTENTS.get(i, "")])
    print("pool size:", len(pool))


if __name__ == "__main__":
    main()
