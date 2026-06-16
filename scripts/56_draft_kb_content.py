# scripts/56_draft_kb_content.py
"""
为高优先 KB 缺口起草证据单元草稿。

流程：
  1. 读取 kb_gap_priority.csv，取 demand>0 且 KB 空白的对
  2. 对每个对调用 DeepSeek，起草 2-3 条符合 evidence_units 格式的证据内容
  3. 写入 data/processed/kb_draft.jsonl（待审核）
  4. 导出 data/processed/kb_draft_review.csv（人工标注列）

审核通过后运行 scripts/57_append_kb_content.py 追加入库。

用法：
  python scripts/56_draft_kb_content.py                   # 所有 demand>0 缺口
  python scripts/56_draft_kb_content.py --top 10          # 只处理 Top N
  python scripts/56_draft_kb_content.py --resume          # 跳过已有草稿的缺口
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS
from cooling_rag_mg.json_utils import loads_lenient

DATA      = PROJECT_ROOT / "data" / "processed"
GAP_CSV   = DATA / "kb_gap_priority.csv"
OUT_JSONL = DATA / "kb_draft.jsonl"
OUT_CSV   = DATA / "kb_draft_review.csv"

_SYSTEM = """你是船舶主机冷却水系统资深工程师，熟悉 CCS、DNV、ABS 规范及 MAN/WinGD/Caterpillar 等主机制造商的设计要求。"""

_USER = """请为以下（部件 × 工程方面）起草 2-3 条**证据内容**，供检索增强生成系统使用。

部件：{comp}（{comp_zh}）
工程方面：{intent}（{intent_zh}）
被以下需求使用：{reqs}

要求：
- 每条证据聚焦该（部件×方面）的一个具体工程规定或设计惯例
- 内容真实、基于船舶工程通行做法，不要杜撰具体法规条文编号
- 语言：中英混合（技术术语用英文，说明用中文）或纯英文均可
- 长度：每条 80-250 字
- 不同条目角度不同（如：一条讲触发条件，一条讲参数要求，一条讲验证方法）

只输出 JSON：
{{"evidences": [
  {{"title": "简短中文标题", "content": "证据文本内容..."}},
  ...
]}}"""


def _draft_for_pair(comp: str, intent: str, reqs: str, client, model: str) -> list[dict]:
    """调用 LLM 起草证据草稿，返回 [{title, content}, ...]"""
    prompt = _USER.format(
        comp=comp, comp_zh=COMPONENTS.get(comp, ""),
        intent=intent, intent_zh=INTENTS.get(intent, ""),
        reqs=reqs,
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        obj = loads_lenient(raw) or {}
        evs = obj.get("evidences", [])
        if not isinstance(evs, list):
            return []
        return [e for e in evs if isinstance(e, dict) and e.get("content")]
    except Exception as ex:
        print(f"    ⚠ LLM error: {ex}")
        return []


def _make_unit(comp: str, intent: str, idx: int, title: str, content: str) -> dict:
    """构建 evidence_unit 格式的草稿字典。"""
    uid = f"E-DRAFT-{comp.upper()[:6]}-{intent.upper()[:8]}-{idx:03d}"
    uid = uid.replace("_", "")[:40]
    return {
        "id": uid,
        "parent_chunk_id": f"CH-DRAFT-{comp}-{intent}-{idx:03d}",
        "text": f"{title}\n{content}",
        "search_text": f"{title}\n{comp} {intent} {COMPONENTS.get(comp,'')} {INTENTS.get(intent,'')}\n{content}",
        "metadata": {
            "topic": title,
            "source_document": "KB_DRAFT_v1",
            "source_type": "project_guide",
            "source_link": "",
            "component_objects": [comp],
            "requirement_intents": [intent],
            "evidence_strength": "indirect",
            "is_generalizable": True,
            "applicability_level": "general",
            "is_noise": False,
            "need_human_review": True,
        },
        "primary_component": comp,
        "primary_intent": intent,
        # review columns (filled by human)
        "_draft_title": title,
        "_draft_status": "pending",   # pending | approved | rejected
        "_draft_note": "",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=0, help="只处理前 N 个缺口（0=全部）")
    ap.add_argument("--resume", action="store_true", help="跳过已有草稿的缺口")
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # 读缺口清单
    with open(GAP_CSV, encoding="utf-8-sig", newline="") as f:
        gaps = [r for r in csv.DictReader(f)
                if int(r["demand"]) > 0 and r["in_kb"] == "False"]
    gaps.sort(key=lambda r: -int(r["demand"]))
    if args.top:
        gaps = gaps[:args.top]
    print(f"待起草缺口: {len(gaps)} 个")

    # 读已有草稿（resume 支持）
    existing: set[tuple[str, str]] = set()
    existing_units: list[dict] = []
    if OUT_JSONL.exists():
        with open(OUT_JSONL, encoding="utf-8") as f:
            for line in f:
                u = json.loads(line)
                existing_units.append(u)
                existing.add((u["primary_component"], u["primary_intent"]))
        if args.resume:
            print(f"Resume: 已有 {len(existing)} 个缺口的草稿，跳过。")

    all_units: list[dict] = list(existing_units)
    n_drafted = 0
    n_skipped = 0

    for i, gap in enumerate(gaps, 1):
        comp   = gap["component"]
        intent = gap["intent"]
        reqs   = gap["requiring_reqs"]
        demand = int(gap["demand"])

        if args.resume and (comp, intent) in existing:
            n_skipped += 1
            continue

        print(f"  [{i:2d}/{len(gaps)}] {comp} × {intent}  (demand={demand}, reqs={reqs})")
        drafts = _draft_for_pair(comp, intent, reqs, client, model)
        if not drafts:
            print(f"    → 起草失败，跳过")
            continue

        for j, d in enumerate(drafts, 1):
            unit = _make_unit(comp, intent, j, d.get("title", f"草稿{j}"), d["content"])
            all_units.append(unit)
            print(f"    [{j}] {d.get('title','?')[:50]}")

        n_drafted += 1
        # 中间落盘
        _flush(all_units, OUT_JSONL)
        time.sleep(0.3)

    _flush(all_units, OUT_JSONL)
    _write_review_csv(all_units, OUT_CSV)

    print(f"\n完成: 起草 {n_drafted} 个缺口，跳过 {n_skipped} 个")
    print(f"草稿文件: {OUT_JSONL}  ({len(all_units)} 条)")
    print(f"审核表格: {OUT_CSV}")
    print("\n人工审核后运行:")
    print("  python scripts/57_append_kb_content.py")


def _flush(units: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")


def _write_review_csv(units: list[dict], path: Path) -> None:
    fields = ["id", "primary_component", "primary_intent",
              "_draft_title", "_draft_status", "_draft_note",
              "text_snippet"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for u in units:
            row = {k: u.get(k, "") for k in fields}
            row["text_snippet"] = u.get("text", "")[:200].replace("\n", " ")
            w.writerow(row)


if __name__ == "__main__":
    main()
