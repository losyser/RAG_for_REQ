# scripts/58_sample_for_expert_review.py
"""
分层抽样：从 60 条需求中选 20 条供专家评审。

四层各 5 条：
  Layer A — 数值密集层：两份输出中具体数字最多的5条（幻觉风险最高）
  Layer B — 安全关键层：涉及停机/冗余/报警设定的5条
  Layer C — 差异最大层：RAG v3 vs no-RAG 文本差异最大的5条
  Layer D — 随机层：    剩余中随机抽5条（避免选择性偏差）

输出：
  data/processed/expert_sample.json  — 20条的详细信息（原始需求+两份输出）
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA = PROJECT_ROOT / "data" / "processed"
EXP  = PROJECT_ROOT / "data" / "search_results" / "exp_v3"

SAFETY_KEYWORDS = {"停机", "保护", "冗余", "报警", "备用", "自动切换",
                   "fail", "trip", "alarm", "redundan", "standby", "auto_start"}


def _shalls_text(result_set: dict) -> str:
    return "\n".join(
        er.get("shall_statement", "")
        for er in result_set.get("engineering_requirements", [])
    )


def _count_numbers(text: str) -> int:
    return len(re.findall(r"\d+\.?\d*\s*(?:MPa|bar|°C|℃|秒|分钟|mm|%|m³|kW|ppm|Hz)", text))


def _edit_distance_approx(a: str, b: str) -> float:
    """Simple character-level divergence (1 - Jaccard on trigrams)."""
    def trigrams(s):
        return {s[i:i+3] for i in range(len(s)-2)}
    ta, tb = trigrams(a), trigrams(b)
    if not ta and not tb:
        return 0.0
    return 1.0 - len(ta & tb) / len(ta | tb)


def main() -> None:
    random.seed(42)

    with open(DATA / "original_requirements_v2.jsonl", encoding="utf-8") as f:
        orig = {json.loads(l)["requirement_id"]: json.loads(l) for l in f}

    with open(EXP / "rag_v3_results.json", encoding="utf-8") as f:
        rag_data = {r["source_requirement_id"]: r
                    for r in json.load(f)["result_sets"]}
    with open(EXP / "norag_results.json", encoding="utf-8") as f:
        norag_data = {r["source_requirement_id"]: r
                      for r in json.load(f)["result_sets"]}

    rids = sorted(set(rag_data) & set(norag_data) & set(orig))
    print(f"可用配对需求: {len(rids)} 条")

    # 预计算各条需求的特征值
    features: dict[str, dict] = {}
    for rid in rids:
        rag_text   = _shalls_text(rag_data[rid])
        norag_text = _shalls_text(norag_data[rid])
        combined   = rag_text + norag_text
        orig_text  = orig[rid].get("requirement_text", "")
        features[rid] = {
            "numeric_count": _count_numbers(combined),
            "is_safety": any(kw in combined.lower() or kw in orig_text
                             for kw in SAFETY_KEYWORDS),
            "divergence":   _edit_distance_approx(rag_text, norag_text),
        }

    # Layer A — 数值密集（排名前5）
    layer_a = sorted(rids, key=lambda r: -features[r]["numeric_count"])[:5]

    # Layer B — 安全关键（排除A，取前5）
    remaining = [r for r in rids if r not in set(layer_a)]
    layer_b = [r for r in sorted(remaining, key=lambda r: -features[r]["is_safety"])
               if features[r]["is_safety"]][:5]
    if len(layer_b) < 5:          # 补足
        layer_b += sorted(
            [r for r in remaining if r not in set(layer_b)],
            key=lambda r: -features[r]["divergence"]
        )[:5 - len(layer_b)]

    # Layer C — 差异最大（排除A/B）
    used = set(layer_a) | set(layer_b)
    layer_c = sorted([r for r in rids if r not in used],
                     key=lambda r: -features[r]["divergence"])[:5]

    # Layer D — 随机（排除A/B/C）
    used |= set(layer_c)
    pool   = [r for r in rids if r not in used]
    layer_d = random.sample(pool, min(5, len(pool)))

    sample = list(dict.fromkeys(layer_a + layer_b + layer_c + layer_d))[:20]
    print(f"\n抽取样本:")
    print(f"  Layer A (数值密集): {layer_a}")
    print(f"  Layer B (安全关键): {layer_b}")
    print(f"  Layer C (差异最大): {layer_c}")
    print(f"  Layer D (随机):     {layer_d}")

    # 构建评审数据（随机打乱A/B标签，不让专家知道哪个是RAG）
    records = []
    for rid in sample:
        req_text = orig[rid].get("requirement_text", "")
        rag_ers  = rag_data[rid].get("engineering_requirements", [])
        norag_ers= norag_data[rid].get("engineering_requirements", [])

        # 随机分配 A/B 标签
        if random.random() < 0.5:
            sys_a, sys_b = "rag_v3", "no_rag"
            ers_a, ers_b = rag_ers, norag_ers
        else:
            sys_a, sys_b = "no_rag", "rag_v3"
            ers_a, ers_b = norag_ers, rag_ers

        records.append({
            "requirement_id":   rid,
            "requirement_text": req_text,
            "stakeholder":      orig[rid].get("stakeholder", ""),
            "layer":            ("A" if rid in layer_a else
                                 "B" if rid in layer_b else
                                 "C" if rid in layer_c else "D"),
            "system_a": sys_a,
            "system_b": sys_b,
            "shalls_a": [er.get("shall_statement", "") for er in ers_a],
            "shalls_b": [er.get("shall_statement", "") for er in ers_b],
            # 评审结果字段（由UI填入）
            "expert1": {d: "" for d in ["decomposition", "accuracy", "traceability",
                                         "completeness", "actionability", "overall", "note"]},
            "expert2": {d: "" for d in ["decomposition", "accuracy", "traceability",
                                         "completeness", "actionability", "overall", "note"]},
            "final":   {d: "" for d in ["decomposition", "accuracy", "traceability",
                                         "completeness", "actionability", "overall", "note"]},
        })

    out = DATA / "expert_sample.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\n样本写入: {out}  ({len(records)} 条)")
    print("\n启动评审界面：")
    print("  python scripts/expert_review_ui.py")
    print("  或双击 expert_review.bat")


if __name__ == "__main__":
    main()
