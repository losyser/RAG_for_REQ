# scripts/57_append_kb_content.py
"""
将人工审核通过的草稿追加到 evidence_units.jsonl，并重建索引。

_draft_status == "approved"  → 追加
_draft_status == "pending"   → 跳过（视为待审核）
_draft_status == "rejected"  → 丢弃

用法：
  python scripts/57_append_kb_content.py --dry-run   # 预览，不写文件
  python scripts/57_append_kb_content.py             # 正式追加
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.evidence_taxonomy import valid_pair

DATA       = PROJECT_ROOT / "data" / "processed"
DRAFT_PATH = DATA / "kb_draft.jsonl"
UNITS_PATH = DATA / "evidence_units.jsonl"
BACKUP     = DATA / "evidence_units.jsonl.before_draft"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not DRAFT_PATH.exists():
        sys.exit(f"找不到 {DRAFT_PATH}，请先运行 scripts/56_draft_kb_content.py")

    with open(DRAFT_PATH, encoding="utf-8") as f:
        drafts = [json.loads(l) for l in f]

    approved = [d for d in drafts if d.get("_draft_status") == "approved"]
    pending  = [d for d in drafts if d.get("_draft_status") in ("pending", "")]
    rejected = [d for d in drafts if d.get("_draft_status") == "rejected"]

    print(f"草稿总数: {len(drafts)}")
    print(f"  approved: {len(approved)}")
    print(f"  pending:  {len(pending)}")
    print(f"  rejected: {len(rejected)}")

    if not approved:
        print("\n没有已批准的草稿，退出。请在 kb_draft_review.csv 中将 _draft_status 改为 approved。")
        return

    # 验证合法性
    invalid = [d for d in approved if not valid_pair(d.get("primary_component", ""), d.get("primary_intent", ""))]
    if invalid:
        print(f"\n⚠ {len(invalid)} 条草稿的 (component, intent) 不在 taxonomy，将跳过：")
        for d in invalid:
            print(f"  {d['id']}: {d['primary_component']} × {d['primary_intent']}")
        approved = [d for d in approved if d not in invalid]

    # 清理内部字段（不写入正式 KB）
    _INTERNAL = {"_draft_title", "_draft_status", "_draft_note"}
    clean = []
    for d in approved:
        u = {k: v for k, v in d.items() if k not in _INTERNAL}
        # 将 need_human_review 改为 False（已审核）
        if isinstance(u.get("metadata"), dict):
            u["metadata"]["need_human_review"] = False
        clean.append(u)

    if args.dry_run:
        print(f"\n[dry-run] 将追加 {len(clean)} 条：")
        for u in clean:
            print(f"  {u['id']}  {u['primary_component']} × {u['primary_intent']}")
            print(f"    {u.get('text','')[:100].replace(chr(10),' ')}")
        return

    # 备份
    import shutil
    shutil.copy2(UNITS_PATH, BACKUP)
    print(f"\n原文件已备份至: {BACKUP}")

    # 追加
    with open(UNITS_PATH, "a", encoding="utf-8") as f:
        for u in clean:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"已追加 {len(clean)} 条到: {UNITS_PATH}")
    print("\n下一步：重建索引")
    print("  python scripts/11_build_multigranular_indexes.py")


if __name__ == "__main__":
    main()
