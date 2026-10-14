# scripts/107_fill_truncated_sets.py
"""Re-generate result sets that came back empty because Stage-4 output was truncated at the
old max_tokens=4000 (finish_reason="length" → invalid JSON → zero shalls).

Only empty sets are regenerated, with the evidence units and extracted values already saved
in the set (_evidence_values), so the evidence is identical; the generator now uses
max_tokens=8192.  Non-empty sets are left untouched: their outputs finished below the old
cap, so a larger cap does not change them.

Usage: PY scripts/107_fill_truncated_sets.py rag|random|rag_qwen
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import classify_result_set

E4 = ROOT / "data/search_results/exp_v4"
FILES = {"rag": "rag_v4_results.json", "random": "ablation_random_retrieval_results.json",
         "rag_qwen": "rag_v4_qwen_results.json"}
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"


def fill_empty_sets(result_sets: list[dict], kb: dict, gen) -> tuple[list[dict], list[str]]:
    """gen(req_id, annotated_units) -> shalls. Returns (new_sets, ids_refilled)."""
    out, filled = [], []
    for rs in result_sets:
        ev = rs.get("_evidence_values") or {}
        if rs.get("engineering_requirements") or not ev:
            out.append(rs)
            continue
        annotated = [{**kb[i], "_extracted_values": vals, "_has_quantitative": bool(vals)}
                     for i, vals in ev.items() if i in kb]
        new = dict(rs)
        t0 = time.perf_counter()
        new["engineering_requirements"] = gen(rs["source_requirement_id"], annotated)
        new["_timing"] = {**rs.get("_timing", {}), "generation_s": round(time.perf_counter() - t0, 3)}
        new["_refilled_max_tokens"] = 8192
        out.append(classify_result_set(new, kb))
        filled.append(rs["source_requirement_id"])
    return out, filled


def main() -> None:
    arm = sys.argv[1]
    from cooling_rag_mg.config import DeepSeekConfig, QwenConfig
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    cfg = QwenConfig() if arm == "rag_qwen" else DeepSeekConfig()
    client = cfg.make_client()
    kb = {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}
    text = {json.loads(l)["requirement_id"]: json.loads(l)["requirement_text"] for l in OR.open(encoding="utf-8")}
    p = E4 / FILES[arm]
    d = json.loads(p.read_text(encoding="utf-8"))
    gen = lambda rid, ann: generate_structured_shalls(source_requirement=text[rid], annotated_evidence=ann,
                                                      client=client, model=cfg.model)
    d["result_sets"], filled = fill_empty_sets(d["result_sets"], kb, gen)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    still = [r["source_requirement_id"] for r in d["result_sets"] if not r["engineering_requirements"]]
    print(arm, "refilled:", filled, "| still empty:", still)


if __name__ == "__main__":
    main()
