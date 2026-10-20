"""
Stage 2.5+3+4 RAG v4：复用 v3 检索结果中的 evidence_ids（v3 agent 归因），
生成结构化 shall，分类 Grade。

输入：data/search_results/exp_v3/rag_v3_results.json
      data/processed/evidence_units_v3_audited.jsonl
      data/processed/original_requirements_v2.jsonl
输出：data/search_results/exp_v4/rag_v4_results.json
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cooling_rag_mg.config import DeepSeekConfig
from cooling_rag_mg.grade_classifier import classify_result_set
from cooling_rag_mg.kb_value_extractor import annotate_evidence_units
from cooling_rag_mg.structured_req_generator import generate_structured_shalls, _build_evidence_block, _MAX_EVIDENCE_ITEMS
from cooling_rag_mg.evidence_contracts import ordered_evidence_ids, select_evidence, SELECTION_POLICY, CONTRACT_VERSION
import hashlib

V3_RAG   = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
EU_JSONL = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OR_JSONL = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT_DIR  = ROOT / "data/search_results/exp_v4"
OUT_FILE = OUT_DIR / "rag_v4_results.json"


def load_eu_index(path: Path) -> dict[str, dict]:
    idx = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            eu = json.loads(line)
            idx[eu["id"]] = eu
    return idx


def load_or_map(path: Path) -> dict[str, str]:
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            result[r["requirement_id"]] = r.get("requirement_text", r["requirement_id"])
    return result


def main():
    cfg = DeepSeekConfig()
    client = cfg.make_client()
    model = cfg.model

    print(f"加载 v3 RAG 结果（{V3_RAG.name}）...")
    with open(V3_RAG, encoding="utf-8") as f:
        v3 = json.load(f)

    print(f"加载证据单元索引（{EU_JSONL.name}）...")
    eu_idx = load_eu_index(EU_JSONL)

    print(f"加载原始需求文本（{OR_JSONL.name}）...")
    or_map = load_or_map(OR_JSONL)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output_result_sets = []
    n_total = len(v3["result_sets"])

    for i, rs in enumerate(v3["result_sets"]):
        or_id = rs["source_requirement_id"]
        stakeholder = rs.get("stakeholder", "")
        source_req_text = or_map.get(or_id, or_id)
        print(f"[{i+1:02d}/{n_total}] {or_id}", end=" ", flush=True)

        # 收集 v3 agent 归因的证据单元（每条 shall 引用的 KB evidence_ids 并集）
        all_eids = ordered_evidence_ids(rs.get("engineering_requirements", []))
        # First saved reference order, not reconstruction of historical retrieval rank.
        evidence_units = [eu_idx[eid] for eid in all_eids if eid in eu_idx]

        # Stage 2.5：值提取标注
        _t0 = time.perf_counter()
        annotated = annotate_evidence_units(evidence_units, client, model)
        _t1 = time.perf_counter()
        n_with_values = sum(1 for eu in annotated if eu["_has_quantitative"])
        print(f"evidence={len(annotated)} with_values={n_with_values}", end=" ", flush=True)

        # Stage 3：结构化 shall 生成
        new_shalls = generate_structured_shalls(
            source_requirement=source_req_text,
            annotated_evidence=annotated,
            client=client,
            model=model,
        )
        _t2 = time.perf_counter()
        print(f"shalls={len(new_shalls)}", end=" ", flush=True)

        # Stage 4：Grade 分类
        new_rs = {
            "source_requirement_id": or_id,
            "stakeholder": stakeholder,
            "_arm": "rag-v4",
            "_n_evidence": len(annotated),
            "_n_with_quantitative": n_with_values,
            "engineering_requirements": new_shalls,
            "_timing": {**rs.get("_timing", {}), "extraction_s": round(_t1 - _t0, 3),
                        "generation_s": round(_t2 - _t1, 3)},
            "_evidence_selection": {"policy": SELECTION_POLICY, "contract_version": CONTRACT_VERSION,
                "input_ids": all_eids, "missing_ids": [eid for eid in all_eids if eid not in eu_idx],
                "selected_ids": [eu["id"] for eu in select_evidence(annotated, _MAX_EVIDENCE_ITEMS)],
                "evidence_block_sha256": hashlib.sha256(_build_evidence_block(annotated).encode("utf-8")).hexdigest()},
            "_extraction_status": {eu["id"]: eu["_extraction_status"] for eu in annotated},
            "_evidence_values": {eu["id"]: eu["_extracted_values"] for eu in annotated},
        }
        classified_rs = classify_result_set(new_rs, eu_idx)
        output_result_sets.append(classified_rs)

        grades = [er["_grade"] for er in classified_rs["engineering_requirements"]]
        gc = Counter(grades)
        print(f"grades={dict(gc)}")

    output = {"arm": "rag-v4", "result_sets": output_result_sets}
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {OUT_FILE}")
    print(f"总 shall 数: {sum(len(rs['engineering_requirements']) for rs in output_result_sets)}")


if __name__ == "__main__":
    main()
