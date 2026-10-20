# scripts/102_leakage_check.py
"""E5：60 条源需求与 KB 的相似度。
对照组：KB 单元与"其他 KB 单元"之间的最近邻相似度，用来说明什么水平才算"近乎复制"。
指标：BGE-M3 最大余弦；最长公共子串（字符数）；源需求中含数字的比例，以及这些数字在 KB 中的命中率。
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.config import get_config
from cooling_rag_mg.index_store import load_sentence_transformer

KB = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT = ROOT / "data/search_results/exp_v4/e5_leakage.json"
NUM = re.compile(r"\d+(?:\.\d+)?")


def lcs_len(a: str, b: str) -> int:
    m = SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return m.size


def main() -> None:
    cfg = get_config()
    kb = [json.loads(l) for l in KB.open(encoding="utf-8")]
    reqs = [json.loads(l) for l in OR.open(encoding="utf-8")]
    model = load_sentence_transformer(cfg.model.embedding_model_path, device=cfg.model.device, label="[E5]")
    kv = model.encode([u["text"][:1000] for u in kb], normalize_embeddings=True, batch_size=32)
    rv = model.encode([r["requirement_text"] for r in reqs], normalize_embeddings=True)
    or_max = (rv @ kv.T).max(axis=1)
    kk = kv @ kv.T
    np.fill_diagonal(kk, -1)
    kb_nn = kk.max(axis=1)
    lcs = [max(lcs_len(r["requirement_text"], u["text"]) for u in kb) for r in reqs]
    kb_nums = {n for u in kb for n in NUM.findall(u["text"])}
    or_nums = [NUM.findall(r["requirement_text"]) for r in reqs]
    res = {"summary": {
        "or_max_cos_median": round(float(np.median(or_max)), 3), "or_max_cos_max": round(float(or_max.max()), 3),
        "kb_nn_cos_median": round(float(np.median(kb_nn)), 3),
        "or_lcs_chars_median": st.median(lcs), "or_lcs_chars_max": max(lcs),
        "or_len_chars_median": st.median(len(r["requirement_text"]) for r in reqs),
        "n_or_with_numbers": sum(1 for x in or_nums if x),
        "or_numbers_found_in_kb": sum(1 for x in or_nums for n in x if n in kb_nums),
        "or_numbers_total": sum(len(x) for x in or_nums)}}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
