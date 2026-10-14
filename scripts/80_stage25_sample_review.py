"""
Stage 2.5 值提取准确率抽样核查脚本。

策略：
  - 按 tier 分层抽样（L1:8 / L2:18 / L3:24 = 50条，比例与KB一致）
  - 在每层内优先保证一半以上来自含数值文本（提高核查效率）
  - 对每条 EU 调用 extract_values_from_evidence，保存原文+提取结果到 CSV

输出：data/search_results/exp_v4/stage25_sample_review.csv
      （用 Excel/WPS 打开，填写 correct_count / missed_count / notes 列）
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cooling_rag_mg.config import DeepSeekConfig
from cooling_rag_mg.kb_value_extractor import extract_values_from_evidence

EU_JSONL = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OUT_DIR  = ROOT / "data/search_results/exp_v4"
OUT_CSV  = OUT_DIR / "stage25_sample_review.csv"

SEED = 42
# 按 tier 比例: L1 213/1349≈8, L2 481/1349≈18, L3 655/1349≈24
TIER_QUOTA = {"L1": 8, "L2": 18, "L3": 24}

_NUM_ROUGH = re.compile(r"\d+\.?\d*")


def load_eus(path: Path) -> dict[str, list[dict]]:
    by_tier: dict[str, list[dict]] = {"L1": [], "L2": [], "L3": []}
    with open(path, encoding="utf-8") as f:
        for line in f:
            eu = json.loads(line)
            tier = eu.get("kb_tier", "")
            if tier in by_tier:
                by_tier[tier].append(eu)
    return by_tier


def stratified_sample(by_tier: dict[str, list[dict]], quota: dict[str, int], seed: int) -> list[dict]:
    rng = random.Random(seed)
    sample = []
    for tier, n in quota.items():
        pool = by_tier.get(tier, [])
        # Split into numeric vs non-numeric
        numeric = [eu for eu in pool if _NUM_ROUGH.search(eu.get("text", ""))]
        non_num = [eu for eu in pool if not _NUM_ROUGH.search(eu.get("text", ""))]
        # Take ~60% from numeric pool, rest from non-numeric
        n_num = min(round(n * 0.6), len(numeric))
        n_non = n - n_num
        picked = rng.sample(numeric, n_num) + rng.sample(non_num, min(n_non, len(non_num)))
        # If non_num pool is small, backfill from numeric
        if len(picked) < n:
            extra = n - len(picked)
            remaining = [eu for eu in numeric if eu not in picked]
            picked += rng.sample(remaining, min(extra, len(remaining)))
        rng.shuffle(picked)
        sample.extend(picked[:n])
    return sample


def format_values(values: list[dict]) -> str:
    if not values:
        return ""
    parts = []
    for v in values:
        op = v.get("operator", "")
        vt = v.get("value_text", "")
        u = v.get("unit", "")
        parts.append(f"{op}{vt}({u})" if op else f"{vt}({u})")
    return " | ".join(parts)


def main():
    cfg = DeepSeekConfig()
    client = cfg.make_client()
    model = cfg.model

    print("Loading evidence units...")
    by_tier = load_eus(EU_JSONL)
    sample = stratified_sample(by_tier, TIER_QUOTA, SEED)
    print(f"Sampled {len(sample)} EUs (L1={sum(1 for e in sample if e['kb_tier']=='L1')}, "
          f"L2={sum(1 for e in sample if e['kb_tier']=='L2')}, "
          f"L3={sum(1 for e in sample if e['kb_tier']=='L3')})")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for i, eu in enumerate(sample, 1):
        eu_id = eu.get("id", "?")
        tier = eu.get("kb_tier", "?")
        source = eu.get("source_document", "?")
        text = eu.get("text", "")
        print(f"[{i:02d}/50] {eu_id} ({tier})", end=" ", flush=True)

        values = extract_values_from_evidence(text, client, model)
        print(f"→ {len(values)} values: {format_values(values)}" if values else "→ (none)")

        rows.append({
            "seq": i,
            "eu_id": eu_id,
            "tier": tier,
            "source_document": source,
            "text": text[:600],
            "extracted_values": format_values(values),
            "n_extracted": len(values),
            # ── 人工核查列（留空） ──────────────────────────────────────
            "correct_count": "",   # 提取正确的数量（≤ n_extracted）
            "missed_count": "",    # 原文中存在但未提取到的数量
            "notes": "",           # 备注（可选）
        })

    fieldnames = ["seq", "eu_id", "tier", "source_document", "text",
                  "extracted_values", "n_extracted",
                  "correct_count", "missed_count", "notes"]

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved → {OUT_CSV}")
    print("请用 Excel/WPS 打开，按列说明填写：")
    print("  correct_count : 提取出来的数值中，真实存在于原文的数量")
    print("  missed_count  : 原文中有明确数值但未被提取到的数量")
    print("  notes         : 可选备注")


if __name__ == "__main__":
    main()
