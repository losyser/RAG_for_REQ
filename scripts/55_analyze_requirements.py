# scripts/55_analyze_requirements.py
"""
对 60 条原始需求逐一运行 requirement_analyzer，统计每个 (component, intent) 对
被需要的次数，与当前 KB 覆盖交叉比对，输出优先缺口清单。

输出：
  data/processed/requirement_pairs.jsonl   ← 每条需求的 (component, intent) 对
  data/processed/kb_gap_priority.csv       ← 按需求覆盖次数排序的缺口清单
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, TAXONOMY, valid_pair
from cooling_rag_mg.requirement_analyzer import analyze_requirement

DATA = PROJECT_ROOT / "data" / "processed"
REQ_PATH  = DATA / "original_requirements_v1.jsonl"
OUT_PAIRS = DATA / "requirement_pairs.jsonl"
OUT_CSV   = DATA / "kb_gap_priority.csv"


def main() -> None:
    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # 读需求
    with open(REQ_PATH, encoding="utf-8") as f:
        reqs = [json.loads(l) for l in f]
    print(f"共 {len(reqs)} 条原始需求")

    # 读当前 KB 覆盖
    ev_path = DATA / "evidence_units.jsonl"
    with open(ev_path, encoding="utf-8") as f:
        units = [json.loads(l) for l in f]
    kb_covered: set[tuple[str, str]] = {
        (u.get("primary_component", ""), u.get("primary_intent", ""))
        for u in units
        if u.get("primary_component") and u.get("primary_intent")
    }
    print(f"KB 当前覆盖 {len(kb_covered)} 个 (component, intent) 对")

    # 逐条分析
    pair_rows: list[dict] = []
    pair_counter: Counter = Counter()
    req_by_pair: dict[tuple, list[str]] = defaultdict(list)

    for i, req in enumerate(reqs, 1):
        rid  = req.get("requirement_id", f"R{i:03d}")
        text = req.get("requirement_text", "")
        pairs = analyze_requirement(text, client, model)
        pair_rows.append({"requirement_id": rid, "text": text,
                          "pairs": [{"component": c, "intent": i2} for c, i2 in pairs]})
        for p in pairs:
            pair_counter[p] += 1
            req_by_pair[p].append(rid)
        print(f"  [{i:2d}/{len(reqs)}] {rid}: {pairs}")
        time.sleep(0.2)

    # 写 per-requirement pairs
    with open(OUT_PAIRS, "w", encoding="utf-8") as f:
        for row in pair_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\n需求对应关系写入: {OUT_PAIRS}")

    # 构建缺口清单（只看 taxonomy 中有定义但 KB 空白的对）
    all_taxonomy_pairs = [(c, i2) for c, intents in TAXONOMY.items() for i2 in intents]
    gap_rows = []
    for (comp, intent) in all_taxonomy_pairs:
        demand = pair_counter.get((comp, intent), 0)
        covered = (comp, intent) in kb_covered
        gap_rows.append({
            "component":    comp,
            "component_zh": COMPONENTS.get(comp, ""),
            "intent":       intent,
            "intent_zh":    INTENTS.get(intent, ""),
            "demand":       demand,         # 被多少条需求需要
            "in_kb":        covered,        # 当前是否有证据
            "requiring_reqs": "|".join(req_by_pair.get((comp, intent), [])),
        })

    # 按优先级排序：需求侧需求量高 + KB 空白 → 最高优先
    gap_rows.sort(key=lambda r: (-r["demand"], r["in_kb"], r["component"], r["intent"]))

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=gap_rows[0].keys())
        writer.writeheader()
        writer.writerows(gap_rows)
    print(f"缺口清单写入: {OUT_CSV}")

    # 打印 Top 20 高优先缺口
    top_gaps = [r for r in gap_rows if not r["in_kb"] and r["demand"] > 0]
    print(f"\n=== Top 高优先缺口（demand>0 且 KB 空白，共 {len(top_gaps)} 个）===")
    print(f"{'component':<30} {'intent':<25} {'需求数':>6}  需求ID")
    print("-" * 85)
    for r in top_gaps[:25]:
        print(f"  {r['component']:<28} {r['intent']:<25} {r['demand']:>4}    {r['requiring_reqs']}")

    covered_demanded = [r for r in gap_rows if r["in_kb"] and r["demand"] > 0]
    print(f"\n已覆盖且有需求: {len(covered_demanded)} 个对")
    not_demanded = [r for r in gap_rows if not r["in_kb"] and r["demand"] == 0]
    print(f"KB空白但无需求: {len(not_demanded)} 个对（低优先）")


if __name__ == "__main__":
    main()
