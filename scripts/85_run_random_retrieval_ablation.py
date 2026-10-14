"""
消融实验：随机检索 vs 语义检索（v4 管道）

目的：验证"语义检索质量"是否有独立贡献。
  - 对每条源需求，从完整KB中随机抽取等量证据单元（不做任何语义匹配）
  - 走同一套 Stage 2.5 + Stage 3 + Stage 4 管道
  - 与 rag_v4_results.json 对比 Grade 分布

预期结论：
  - Grade X 仍为 0%（citation constraint 负责消除 Grade X）
  - Grade A+B 显著下降（随机证据命中精确值的概率低）
  - Grade C 显著上升（更多 honest deferral）
  → 说明语义检索对"有用的接地数值"有独立贡献

输入：
  data/search_results/exp_v4/rag_v4_results.json   （取各OR的证据数量 _n_evidence）
  data/processed/evidence_units_v3_audited.jsonl
  data/processed/original_requirements_v2.jsonl
输出：
  data/search_results/exp_v4/ablation_random_retrieval_results.json
  data/search_results/exp_v4/ablation_random_retrieval_summary.json
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cooling_rag_mg.config import DeepSeekConfig
from cooling_rag_mg.grade_classifier import classify_result_set
from cooling_rag_mg.kb_value_extractor import annotate_evidence_units
from cooling_rag_mg.structured_req_generator import generate_structured_shalls

EXP_DIR  = ROOT / "data/search_results/exp_v4"
RAG_FILE = EXP_DIR / "rag_v4_results.json"
EU_JSONL = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OR_JSONL = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT_FILE = EXP_DIR / "ablation_random_retrieval_results.json"
SUM_FILE = EXP_DIR / "ablation_random_retrieval_summary.json"

SEED = 42


def load_eu_list(path: Path) -> list[dict]:
    eus = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            eus.append(json.loads(line))
    return eus


def load_or_map(path: Path) -> dict[str, str]:
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            result[r["requirement_id"]] = r.get("requirement_text", r["requirement_id"])
    return result


def compute_metrics(result_sets: list[dict], arm: str) -> dict:
    shalls = []
    for rs in result_sets:
        for er in rs.get("engineering_requirements", []):
            er_copy = dict(er)
            er_copy["_or_id"] = rs["source_requirement_id"]
            shalls.append(er_copy)

    n = len(shalls)
    if n == 0:
        return {"arm": arm, "n_shalls": 0}

    grade_counts = Counter(er.get("_grade", "?") for er in shalls)
    cited    = sum(1 for er in shalls if er.get("evidence_citations"))
    has_l1   = sum(1 for er in shalls
                   if any(c.get("tier") == "L1" for c in er.get("evidence_citations", [])))
    multi_src = sum(1 for er in shalls if len(er.get("evidence_citations", [])) >= 2)

    return {
        "arm": arm,
        "n_shalls": n,
        "grade_A": grade_counts.get("A", 0),
        "grade_B": grade_counts.get("B", 0),
        "grade_C": grade_counts.get("C", 0),
        "grade_X": grade_counts.get("X", 0),
        "grade_A_pct": round(grade_counts.get("A", 0) / n * 100, 1),
        "grade_B_pct": round(grade_counts.get("B", 0) / n * 100, 1),
        "grade_C_pct": round(grade_counts.get("C", 0) / n * 100, 1),
        "grade_X_pct": round(grade_counts.get("X", 0) / n * 100, 1),
        "citation_rate_pct":    round(cited     / n * 100, 1),
        "l1_citation_rate_pct": round(has_l1    / n * 100, 1),
        "multi_source_rate_pct": round(multi_src / n * 100, 1),
    }


def main():
    rng = random.Random(SEED)

    cfg = DeepSeekConfig()
    client = cfg.make_client()
    model = cfg.model

    print(f"加载 KB 全量证据单元（{EU_JSONL.name}）...")
    all_eus = load_eu_list(EU_JSONL)
    print(f"  共 {len(all_eus)} 条")

    print(f"加载原始需求文本（{OR_JSONL.name}）...")
    or_map = load_or_map(OR_JSONL)

    print(f"加载 RAG v4 结果（获取各OR证据数量）...")
    with open(RAG_FILE, encoding="utf-8") as f:
        rag_data = json.load(f)

    # 建立 OR → 证据数量映射（保持与 RAG 等量，最少 4 条）
    rag_n_evidence: dict[str, int] = {}
    for rs in rag_data["result_sets"]:
        n = max(rs.get("_n_evidence", 4), 4)
        rag_n_evidence[rs["source_requirement_id"]] = n

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    output_result_sets = []
    n_total = len(rag_data["result_sets"])

    for i, rs in enumerate(rag_data["result_sets"]):
        or_id = rs["source_requirement_id"]
        stakeholder = rs.get("stakeholder", "")
        source_req_text = or_map.get(or_id, or_id)
        n_ev = rag_n_evidence[or_id]

        # 从全量KB随机抽取等量证据单元
        sampled_eus = rng.sample(all_eus, min(n_ev, len(all_eus)))
        print(f"[{i+1:02d}/{n_total}] {or_id}  random_evidence={len(sampled_eus)}", end=" ", flush=True)

        # Stage 2.5：值提取标注
        annotated = annotate_evidence_units(sampled_eus, client, model)
        n_with_values = sum(1 for eu in annotated if eu["_has_quantitative"])
        print(f"with_values={n_with_values}", end=" ", flush=True)

        # Stage 3：结构化 shall 生成
        new_shalls = generate_structured_shalls(
            source_requirement=source_req_text,
            annotated_evidence=annotated,
            client=client,
            model=model,
        )
        print(f"shalls={len(new_shalls)}", end=" ", flush=True)

        # Stage 4：Grade 分类
        new_rs = {
            "source_requirement_id": or_id,
            "stakeholder": stakeholder,
            "_arm": "random-retrieval-v4",
            "_n_evidence": len(annotated),
            "_n_with_quantitative": n_with_values,
            "engineering_requirements": new_shalls,
        }
        classified_rs = classify_result_set(new_rs)
        output_result_sets.append(classified_rs)

        grades = [er["_grade"] for er in classified_rs["engineering_requirements"]]
        gc = Counter(grades)
        print(f"grades={dict(gc)}")

    output = {"arm": "random-retrieval-v4", "result_sets": output_result_sets}
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {OUT_FILE}")

    # 对比汇总
    rag_metrics  = compute_metrics(rag_data["result_sets"], "rag-v4 (semantic)")
    rand_metrics = compute_metrics(output_result_sets, "random-retrieval-v4")

    # 同时加载 no-RAG 作为三方对比
    nor_file = EXP_DIR / "norag_v4_results.json"
    if nor_file.exists():
        with open(nor_file, encoding="utf-8") as f:
            nor_data = json.load(f)
        nor_metrics = compute_metrics(nor_data["result_sets"], "norag-v4")
    else:
        nor_metrics = {}

    summary = {
        "rag_semantic": rag_metrics,
        "random_retrieval": rand_metrics,
        "norag": nor_metrics,
    }
    with open(SUM_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 打印三方对比
    print("\n" + "="*60)
    print("三方对比（Grade X 消融分析）")
    print("="*60)
    header = f"{'指标':<20} {'语义RAG':>12} {'随机检索':>12} {'no-RAG':>10}"
    print(header)
    print("-"*60)
    for key, label in [
        ("grade_X_pct",         "Grade X %"),
        ("grade_A_pct",         "Grade A %"),
        ("grade_B_pct",         "Grade B %"),
        ("grade_C_pct",         "Grade C %"),
        ("l1_citation_rate_pct","L1引用率 %"),
        ("n_shalls",            "Shall总数"),
    ]:
        rv = rag_metrics.get(key, "—")
        rdv = rand_metrics.get(key, "—")
        nv = nor_metrics.get(key, "—")
        print(f"{label:<20} {str(rv):>12} {str(rdv):>12} {str(nv):>10}")

    print(f"\n已保存对比汇总 → {SUM_FILE}")


if __name__ == "__main__":
    main()
