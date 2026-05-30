# scripts/42_split_requirements.py
# -*- coding: utf-8 -*-
"""Phase 1 Task 1.4：用 DeepSeek 把冻结的原始需求拆成共享子需求。

多智能体分工中的「拆分」角色（DeepSeek）。产物 split_requirements_v1.jsonl 为
**两实验组(B0/R)共用**的子需求拆分——这是单变量设计的前提：拆分固定，只变检索。

用法：
  python scripts/42_split_requirements.py
  python scripts/42_split_requirements.py --in data/processed/original_requirements_v1.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
from cooling_rag_mg.requirement_splitter import split_requirement


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default=None,
                    help="原始需求 jsonl（缺省 processed/original_requirements_v1.jsonl）")
    ap.add_argument("--out", default=None,
                    help="输出 jsonl（缺省 processed/split_requirements_v1.jsonl）")
    args = ap.parse_args()

    cfg = get_config()
    if not (cfg.deepseek.enabled and cfg.deepseek.use_requirement_splitter):
        print("DeepSeek 未配置或拆分器被禁用（.env）。"); sys.exit(1)

    in_path = Path(args.in_path) if args.in_path else cfg.paths.processed_dir / "original_requirements_v1.jsonl"
    out_path = Path(args.out) if args.out else cfg.paths.processed_dir / "split_requirements_v1.jsonl"
    if not in_path.exists():
        print(f"未找到原始需求：{in_path}。先运行 scripts/41。"); sys.exit(1)

    originals = list(read_jsonl(in_path))
    print(f"[split] {len(originals)} 条原始需求，开始 DeepSeek 拆分（含审核循环）...")

    records = []
    sub_counts = []
    fallback_n = 0
    for i, r in enumerate(originals, start=1):
        rid = r["requirement_id"]
        subs = split_requirement(rid, r.get("stakeholder", ""), r.get("requirement_text", ""))
        # 标准化子需求 id 为 {src}-{nn}
        for j, s in enumerate(subs, start=1):
            s["sub_requirement_id"] = f"{rid}-{j:02d}"
        if any(s.get("split_method", "").startswith("fallback") for s in subs):
            fallback_n += 1
        sub_counts.append(len(subs))
        records.append({
            "source_requirement_id": rid,
            "stakeholder": r.get("stakeholder", ""),
            "requirement_text": r.get("requirement_text", ""),
            "sub_requirements": subs,
        })
        print(f"  [{i}/{len(originals)}] {rid} → {len(subs)} 子需求")

    write_jsonl(out_path, records)
    total = sum(sub_counts)
    avg = total / len(sub_counts) if sub_counts else 0
    print(f"\n拆分完成：{len(records)} 条原始 → 共 {total} 子需求"
          f"（均 {avg:.1f}/条，min {min(sub_counts)} max {max(sub_counts)}）")
    if fallback_n:
        print(f"[note] {fallback_n} 条走了 fallback 规则拆分（DeepSeek 异常/未通过审核）。")
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
