"""
no-RAG v4 基线：无检索证据，结构化 prompt，输出 Grade 分布。
输出：data/search_results/exp_v4/norag_v4_qwen_results.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cooling_rag_mg.config import QwenConfig
from cooling_rag_mg.structured_req_generator import generate_norag_shalls
from cooling_rag_mg.grade_classifier import classify_result_set

OR_JSONL = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT_DIR  = ROOT / "data/search_results/exp_v4"
OUT_FILE = OUT_DIR / "norag_v4_qwen_results.json"


def load_requirements(path: Path) -> list[dict]:
    reqs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            reqs.append(json.loads(line))
    return reqs


def main():
    cfg = QwenConfig()
    client = cfg.make_client()
    model = cfg.model

    reqs = load_requirements(OR_JSONL)
    print(f"Loaded {len(reqs)} source requirements")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    output_result_sets = []

    for i, req in enumerate(reqs):
        or_id = req["requirement_id"]
        text = req.get("requirement_text", or_id)
        stakeholder = req.get("stakeholder", "")
        print(f"[{i+1:02d}/{len(reqs)}] {or_id}", end=" ", flush=True)

        shalls = generate_norag_shalls(text, client, model)
        print(f"shalls={len(shalls)}", end=" ", flush=True)

        rs = {
            "source_requirement_id": or_id,
            "stakeholder": stakeholder,
            "_arm": "norag-v4",
            "engineering_requirements": shalls,
        }
        classified_rs = classify_result_set(rs)
        output_result_sets.append(classified_rs)

        grades = [er["_grade"] for er in classified_rs["engineering_requirements"]]
        gc = Counter(grades)
        print(f"grades={dict(gc)}")

    output = {"arm": "norag-v4", "result_sets": output_result_sets}
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUT_FILE}")
    print(f"Total shalls: {sum(len(rs['engineering_requirements']) for rs in output_result_sets)}")


if __name__ == "__main__":
    main()
