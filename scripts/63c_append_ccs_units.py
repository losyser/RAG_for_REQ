"""
将审核通过的 ccs_l1_units.jsonl 追加到 evidence_units.jsonl，并重建索引。

用法:
  python scripts/63c_append_ccs_units.py --dry-run   # 预览
  python scripts/63c_append_ccs_units.py             # 正式追加
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA      = PROJECT_ROOT / "data" / "processed"
DRAFT     = DATA / "ccs_l1_units.jsonl"
UNITS     = DATA / "evidence_units.jsonl"
BACKUP    = DATA / "evidence_units.jsonl.before_ccs"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all",     action="store_true", help="追加所有单元（不过滤status）")
    args = ap.parse_args()

    if not DRAFT.exists():
        sys.exit("未找到 %s，请先运行 scripts/63b_extract_ccs_targeted.py" % DRAFT)

    with open(DRAFT, encoding="utf-8") as f:
        drafts = [json.loads(l) for l in f]

    if args.all:
        approved = drafts
    else:
        approved = [d for d in drafts if d.get("_draft_status") == "approved"]
        pending  = [d for d in drafts if d.get("_draft_status","pending") == "pending"]
        rejected = [d for d in drafts if d.get("_draft_status") == "rejected"]
        print("草稿总数: %d  (approved=%d, pending=%d, rejected=%d)" % (
            len(drafts), len(approved), len(pending), len(rejected)))

    if not approved:
        print("\n没有已批准的草稿。")
        print("请在 ccs_l1_review.csv 中将 _draft_status 改为 approved，")
        print("或使用 --all 直接追加所有草稿（建议先人工审核）。")
        return

    # 清理内部字段
    _INTERNAL = {"_draft_status", "_draft_note"}
    clean = []
    for d in approved:
        u = {k: v for k, v in d.items() if k not in _INTERNAL}
        if isinstance(u.get("metadata"), dict):
            u["metadata"]["need_human_review"] = False
        clean.append(u)

    if args.dry_run:
        print("\n[dry-run] 将追加 %d 条L1单元:" % len(clean))
        for u in clean[:10]:
            print("  %s | %s × %s | %s" % (
                u["id"], u["primary_component"], u["primary_intent"],
                u.get("text","")[:50].replace("\n"," ")))
        if len(clean) > 10:
            print("  ... 和另外 %d 条" % (len(clean)-10))
        return

    # 备份
    if not BACKUP.exists():
        shutil.copy2(UNITS, BACKUP)
        print("备份: %s" % BACKUP.name)

    # 追加
    with open(UNITS, "a", encoding="utf-8") as f:
        for u in clean:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print("已追加 %d 条L1单元到 evidence_units.jsonl" % len(clean))

    # 重建索引
    print("\n重建索引...")
    import subprocess
    r = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "11_build_multigranular_indexes.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if r.returncode == 0:
        print("Index rebuild done.")
    else:
        print("Index rebuild failed. Run manually: python scripts/11_build_multigranular_indexes.py")
        print(r.stderr[-300:])

if __name__ == "__main__":
    main()
