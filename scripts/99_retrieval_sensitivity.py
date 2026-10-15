# scripts/99_retrieval_sensitivity.py
"""E3 敏感性分析。
--part boundary  ：切分边界分析和截断分析（不调 LLM）
--part retrieval ：用固定的 pairs（取自 Task 6 重跑的 _pairs_used）跑各检索变体，计算检索层指标（不调 LLM）
--part e2e --variant <名称> ：对单个变体跑端到端（证据选择 T=0 → Stage 3 → Stage 4 → 以 KB 为准分级）
--part summary   ：汇总，生成 summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.config import get_config
from cooling_rag_mg.grade_classifier import classify_result_set
from cooling_rag_mg.index_store import HybridIndexSearcher, build_index, load_index
from cooling_rag_mg.retrieval_variants import boundary_split_rate, retrieve_for_pairs

KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
V3 = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
V4 = ROOT / "data/search_results/exp_v4/rag_v4_results.json"
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT = ROOT / "data/search_results/exp_v4/sensitivity"
ALT_IDX = ROOT / "data/indexes/evidence_units_mpnet"
NUMV = re.compile(r"\d+(?:\.\d+)?\s*(?:°C|℃|MPa|bar|kPa|%|s\b|秒|min|m³/h|L/min|rpm|kW|mm)")
VARIANTS = {
    "default": dict(mode="hybrid"), "vector_only": dict(mode="vector"), "bm25_only": dict(mode="bm25"),
    "w_bm25_0.25": dict(mode="hybrid", w_bm25=0.25), "w_bm25_0.75": dict(mode="hybrid", w_bm25=0.75),
    "k0_10": dict(mode="hybrid", k0=10), "k0_100": dict(mode="hybrid", k0=100),
    "k_4": dict(mode="hybrid", per_pair_k=4), "k_12": dict(mode="hybrid", per_pair_k=12),
    "embed_mpnet": dict(mode="hybrid", _index="mpnet"),
}
E2E = ["vector_only", "bm25_only", "embed_mpnet", "trunc_1200"]


def _kb():
    return {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}


def _pairs():
    v3 = json.loads(V3.read_text(encoding="utf-8"))
    return {rs["source_requirement_id"]: [tuple(p.split("×")) for p in rs.get("_pairs_used", [])]
            for rs in v3["result_sets"]}


def index_ready(d: Path) -> bool:
    """索引目录是否已建成。build_index 现在写 vectors.npy（NumpyFlatIP），
    不再写 faiss.index，因此以此为准。"""
    d = Path(d)
    return (d / "vectors.npy").exists() and (d / "records.pkl").exists()


def _searcher(name: str, cfg):
    if name == "mpnet":
        if not index_ready(ALT_IDX):
            build_index(jsonl_path=KBP, output_dir=ALT_IDX, text_field="search_text",
                        model_path="D:/models/mpnet-multilingual", device="cpu", normalize=True)
        return HybridIndexSearcher(load_index(ALT_IDX), device="cpu")
    return HybridIndexSearcher(load_index(ROOT / "data/indexes/evidence_units"), device="cpu")


def part_boundary() -> dict:
    kb = _kb()
    v4 = json.loads(V4.read_text(encoding="utf-8"))
    used = {i for rs in v4["result_sets"] for i in rs.get("_evidence_values", {})}
    texts = [kb[i]["text"] for i in used if i in kb]
    lim = int(os.getenv("RAG_EU_TEXT_LIMIT", "500"))
    res = {"n_used_units": len(texts),
           "pct_used_units_longer_than_prompt_limit": round(sum(len(t) > lim for t in texts) / len(texts) * 100, 1),
           "pct_values_beyond_prompt_limit": round(
               sum(1 for t in texts for m in NUMV.finditer(t) if m.start() >= lim) /
               max(1, sum(1 for t in texts for _ in NUMV.finditer(t))) * 100, 1),
           "eu_atomic": boundary_split_rate(texts, window=10**6, overlap=0.0),
           "fixed_windows": [boundary_split_rate(texts, w, o) for w in (128, 256, 512) for o in (0.0, 0.2)]}
    return res


def part_retrieval(cfg) -> dict:
    kb, pairs = _kb(), _pairs()
    text = {json.loads(l)["requirement_id"]: json.loads(l)["requirement_text"] for l in OR.open(encoding="utf-8")}
    searchers = {"default": _searcher("default", cfg)}
    sets: dict[str, dict[str, list[str]]] = {}
    t_enc = {}
    for name, kw in VARIANTS.items():
        kw = dict(kw); idx = kw.pop("_index", "default")
        if idx not in searchers:
            searchers[idx] = _searcher(idx, cfg)
        s = searchers[idx]
        sets[name] = {}
        t0 = time.perf_counter()
        for rid, ps in pairs.items():
            sets[name][rid] = [r["id"] for r in retrieve_for_pairs(text[rid], ps, s, **kw)] if ps else []
        t_enc[name] = round((time.perf_counter() - t0) / max(1, len(pairs)), 3)
    def jac(a, b):
        a, b = set(a), set(b); return len(a & b) / len(a | b) if a | b else 1.0
    out = {}
    for name, d in sets.items():
        ids = [i for v in d.values() for i in v]
        out[name] = {
            "jaccard_vs_default_mean": round(st.mean(jac(d[r], sets["default"][r]) for r in d), 3),
            "units_per_req_mean": round(st.mean(len(v) for v in d.values()), 2),
            "l1_share_pct": round(sum(kb[i]["kb_tier"] == "L1" for i in ids) / max(1, len(ids)) * 100, 1),
            "numeric_unit_share_pct": round(sum(bool(NUMV.search(kb[i]["text"])) for i in ids) / max(1, len(ids)) * 100, 1),
            "sec_per_req_cpu_query": t_enc[name]}
    (OUT / "retrieval_sets.json").write_text(json.dumps(sets, ensure_ascii=False), encoding="utf-8")
    return out


def part_e2e(variant: str, cfg) -> None:
    from cooling_rag_mg.kb_value_extractor import annotate_evidence_units
    from cooling_rag_mg.req_generation_v2 import generate_rag_v3
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    kb, pairs = _kb(), _pairs()
    text = {json.loads(l)["requirement_id"]: json.loads(l)["requirement_text"] for l in OR.open(encoding="utf-8")}
    client, model = cfg.deepseek.make_client(), cfg.deepseek.model
    if variant == "trunc_1200":
        os.environ["RAG_EU_TEXT_LIMIT"] = "1200"; os.environ["RAG_EXTRACT_CHAR_LIMIT"] = "2400"
        import importlib, cooling_rag_mg.structured_req_generator as sg
        importlib.reload(sg); generate_structured_shalls = sg.generate_structured_shalls
        v3 = json.loads(V3.read_text(encoding="utf-8"))
        selected = {rs["source_requirement_id"]: sorted({i for er in rs["engineering_requirements"]
                                                          for i in er.get("evidence_ids", [])})
                    for rs in v3["result_sets"]}
    else:
        sets = json.loads((OUT / "retrieval_sets.json").read_text(encoding="utf-8"))[variant]
        selected = {}
    out = []
    for rid in sorted(text):
        if variant != "trunc_1200":
            ev = [kb[i] for i in sets.get(rid, []) if i in kb]
            ers = generate_rag_v3(text[rid], ev, client, model, temperature=0.0) if ev else []
            selected[rid] = sorted({i for er in ers for i in er.get("evidence_ids", [])})
        eus = [kb[i] for i in selected[rid] if i in kb]
        ann = annotate_evidence_units(eus, client, model)
        shalls = generate_structured_shalls(source_requirement=text[rid], annotated_evidence=ann,
                                            client=client, model=model) if ann else []
        out.append(classify_result_set({"source_requirement_id": rid, "_n_evidence": len(ann),
                                        "engineering_requirements": shalls}, kb))
        print(variant, rid, len(shalls), flush=True)
    (OUT / f"{variant}_results.json").write_text(
        json.dumps({"arm": variant, "result_sets": out}, ensure_ascii=False, indent=1), encoding="utf-8")


def part_summary() -> dict:
    spec = __import__("importlib.util").util.spec_from_file_location("pn", ROOT / "scripts/100_paper_numbers.py")
    pn = __import__("importlib.util").util.module_from_spec(spec); spec.loader.exec_module(pn)
    kb = _kb()
    res = {"boundary": json.loads((OUT / "boundary.json").read_text(encoding="utf-8")),
           "retrieval": json.loads((OUT / "retrieval.json").read_text(encoding="utf-8")),
           "e2e": {"default": pn.grade_summary(json.loads(V4.read_text(encoding="utf-8")), kb)}}
    for v in E2E:
        p = OUT / f"{v}_results.json"
        if p.exists():
            res["e2e"][v] = pn.grade_summary(json.loads(p.read_text(encoding="utf-8")), kb)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["boundary", "retrieval", "e2e", "summary"])
    ap.add_argument("--variant", default="")
    a = ap.parse_args()
    cfg = get_config(); OUT.mkdir(parents=True, exist_ok=True)
    if a.part == "boundary":
        r = part_boundary(); (OUT / "boundary.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    elif a.part == "retrieval":
        r = part_retrieval(cfg); (OUT / "retrieval.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    elif a.part == "e2e":
        assert a.variant in E2E, f"variant must be one of {E2E}"
        part_e2e(a.variant, cfg); r = {"done": a.variant}
    else:
        r = part_summary(); (OUT / "summary.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
