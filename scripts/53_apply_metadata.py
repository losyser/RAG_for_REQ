# scripts/53_apply_metadata.py
"""
将 script 52 生成的重标注结果合并回 evidence_units.jsonl。

每条记录写入两个字段：
  primary_component  — 新 taxonomy 的精确部件
  primary_intent     — 新 taxonomy 的精确方面

原有的 component_objects / requirement_intents 字段保持不变（兼容旧代码）。
重建索引请再执行 python scripts/11_build_multigranular_indexes.py。

用法：
  python scripts/53_apply_metadata.py              # 正式合并
  python scripts/53_apply_metadata.py --dry-run    # 只打印差异，不写文件
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.evidence_taxonomy import valid_pair

DATA        = PROJECT_ROOT / "data" / "processed"
UNITS_PATH  = DATA / "evidence_units.jsonl"
ENRICHED    = DATA / "metadata_enriched.jsonl"
BACKUP      = DATA / "evidence_units.jsonl.bak"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="只报告差异，不写入文件")
    args = ap.parse_args()

    if not ENRICHED.exists():
        sys.exit(f"找不到 {ENRICHED}，请先运行 scripts/52_enrich_metadata.py")

    # ── 读入重标注结果 ──
    enriched: dict[str, dict] = {}
    with open(ENRICHED, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            enriched[r["id"]] = r

    # ── 读入原始 evidence_units ──
    units: list[dict] = []
    with open(UNITS_PATH, encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))

    # ── 验证 & 统计差异 ──
    changed = 0
    invalid = 0
    missing = 0
    for u in units:
        uid = u["id"]
        if uid not in enriched:
            missing += 1
            continue
        r = enriched[uid]
        comp   = r.get("primary_component", "")
        intent = r.get("primary_intent", "")

        if not valid_pair(comp, intent):
            print(f"  ⚠ {uid}: ({comp}, {intent}) 不在 taxonomy，跳过")
            invalid += 1
            continue

        old_comp   = u.get("primary_component", "")
        old_intent = u.get("primary_intent", "")
        if comp != old_comp or intent != old_intent:
            changed += 1
            if args.dry_run:
                print(f"  {uid}: ({old_comp},{old_intent}) → ({comp},{intent})")

    print(f"总条目:   {len(units)}")
    print(f"有重标注: {len(enriched)}")
    print(f"将更新:   {changed}")
    print(f"无重标注: {missing}（保持原样）")
    print(f"无效对:   {invalid}（跳过）")

    if args.dry_run:
        print("\n[dry-run] 未写入任何文件。")
        return

    # ── 备份原文件 ──
    import shutil
    shutil.copy2(UNITS_PATH, BACKUP)
    print(f"\n原文件已备份至: {BACKUP}")

    # ── 写入更新后的 evidence_units.jsonl ──
    with open(UNITS_PATH, "w", encoding="utf-8") as f:
        for u in units:
            uid = u["id"]
            if uid in enriched:
                r = enriched[uid]
                comp   = r.get("primary_component", "")
                intent = r.get("primary_intent", "")
                if valid_pair(comp, intent):
                    u["primary_component"] = comp
                    u["primary_intent"]    = intent
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    print(f"已写入: {UNITS_PATH}（{changed} 条更新）")
    print("\n下一步：重建索引")
    print("  python scripts/11_build_multigranular_indexes.py")


if __name__ == "__main__":
    main()
