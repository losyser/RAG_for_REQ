"""
Phase 3: 对现有 1307 个 evidence_units 进行 L1/L2/L3 知识层级分级。

L1 (监管层): 来自船级社规则(CCS/DNV/ABS/IACS/SOLAS/MARPOL)的强制要求，含
            "shall/must/不得/应不少于" 等具有法律约束力的语言。
L2 (参数层): 有具体数值约束、接受标准或量化限值的技术规范或设备参数，
            非强制但提供明确设计约束。
L3 (背景层): 描述性内容、安装操作步骤、维护建议等无约束力的工程经验。

输出:
  data/processed/evidence_units_tiered.jsonl  ← 原 JSONL + kb_tier + tier_reason 字段
  data/processed/tier_stats.json             ← 分级统计报告
  data/processed/tier_review.csv             ← 人工抽查表（L1单元）

用法:
  python scripts/62_tier_kb_units.py
  python scripts/62_tier_kb_units.py --resume      # 跳过已分级的单元
  python scripts/62_tier_kb_units.py --dry-run 20  # 只跑前20条预览
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.json_utils import loads_lenient

DATA       = PROJECT_ROOT / "data" / "processed"
UNITS_PATH = DATA / "evidence_units.jsonl"
OUT_TIERED = DATA / "evidence_units_tiered.jsonl"
OUT_STATS  = DATA / "tier_stats.json"
OUT_CSV    = DATA / "tier_review.csv"

# 快速规则预分级：节省 API 调用
SHIP_RULE_TYPES = {"ship_rule", "class_rule"}
STANDARD_TYPES  = {"standard", "imo_resolution", "convention"}

REGULATORY_KEYWORDS = [
    "shall", "must", "shall not", "must not", "required", "mandatory",
    "不得低于", "不得超过", "不得少于", "应不少于", "应不超过",
    "应具备", "应设置", "必须", "不允许", "严禁",
]

SYSTEM_PROMPT = """\
你是船舶工程合规专家，负责将证据单元分入知识层级：

L1（监管层）：来自船级社规则（CCS/DNV/ABS/Lloyd's/IACS）、国际公约（SOLAS/MARPOL）或IMO决议的强制要求。
  特征：含"shall/must/不得/应不少于/应不超过"等强制语言，具有法律约束力，审查员会直接核对。
  来源类型：ship_rule, class_rule, standard, convention

L2（参数层）：含具体数值限值、量化接受标准或工程边界的技术内容。
  特征：有具体温度/压力/流量数值或明确接受标准，但非强制性规范条文。
  来源类型：project_guide（含参数表）、standard（参数部分）、spec_sheet

L3（背景层）：描述性/操作性内容，无约束力。
  特征：安装步骤、维护建议、系统组成描述、工作原理说明、故障排除指南。

只输出JSON: {"tier": 1|2|3, "reason": "一句话理由（中文，15字内）"}"""


def _quick_tier(unit: dict) -> int | None:
    """规则预分级：有把握时返回1/2/3，不确定时返回None（交LLM判断）"""
    meta = unit.get("metadata", {})
    src_type = meta.get("source_type", "").lower()
    text = unit.get("text", "").lower()

    # ship_rule 且含强制语言 → L1
    if src_type in SHIP_RULE_TYPES:
        for kw in REGULATORY_KEYWORDS:
            if kw.lower() in text:
                return 1
        return 1  # 船级社规则即使描述性也归L1

    # standard → L1 或 L2，交LLM判断
    if src_type in STANDARD_TYPES:
        return None

    # installation_guide + engine_manual → 通常L3，但含强制语言时交LLM
    if src_type in {"installation_guide", "engine_manual"}:
        for kw in REGULATORY_KEYWORDS:
            if kw.lower() in text:
                return None  # 含强制语言，交LLM
        return 3

    return None  # project_guide 等，交LLM


def _llm_tier(unit: dict, client, model: str) -> dict:
    """调用 LLM 分级，返回 {tier, reason}"""
    meta = unit.get("metadata", {})
    src_doc = meta.get("source_document", "")[:60]
    src_type = meta.get("source_type", "")
    intents = meta.get("requirement_intents", [])
    text_excerpt = unit.get("text", "")[:300]

    user_msg = (
        f"来源类型: {src_type}\n"
        f"文档: {src_doc}\n"
        f"工程意图: {intents}\n"
        f"内容摘录:\n{text_excerpt}"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=80,
        )
        raw = resp.choices[0].message.content or "{}"
        obj = loads_lenient(raw) or {}
        tier = obj.get("tier")
        if tier not in (1, 2, 3):
            tier = int(tier) if str(tier) in ("1", "2", "3") else 3
        return {"tier": tier, "reason": obj.get("reason", "LLM判定")}
    except Exception as ex:
        return {"tier": 3, "reason": f"API错误: {str(ex)[:30]}"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true", help="跳过已分级的单元")
    ap.add_argument("--dry-run", type=int, default=0, metavar="N", help="只处理前N条")
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # 读现有单元
    with open(UNITS_PATH, encoding="utf-8") as f:
        units = [json.loads(l) for l in f]

    # resume：读取已分级结果
    already_tiered: dict[str, dict] = {}
    if args.resume and OUT_TIERED.exists():
        with open(OUT_TIERED, encoding="utf-8") as f:
            for line in f:
                u = json.loads(line)
                if "kb_tier" in u:
                    already_tiered[u["id"]] = u
        print(f"Resume: 已有 {len(already_tiered)} 条分级结果")

    if args.dry_run:
        units = units[:args.dry_run]
        print(f"[dry-run] 仅处理前 {args.dry_run} 条")

    tiered_units: list[dict] = []
    n_rule  = 0
    n_llm   = 0
    n_skip  = 0

    for i, unit in enumerate(units, 1):
        uid = unit["id"]

        # resume 跳过
        if uid in already_tiered:
            tiered_units.append(already_tiered[uid])
            n_skip += 1
            continue

        # 规则预分级
        quick = _quick_tier(unit)
        if quick is not None:
            unit = {**unit, "kb_tier": quick, "tier_reason": f"规则: {unit['metadata'].get('source_type','')}"}
            n_rule += 1
        else:
            result = _llm_tier(unit, client, model)
            unit = {**unit, "kb_tier": result["tier"], "tier_reason": result["reason"]}
            n_llm += 1
            time.sleep(0.05)  # 限速

        tiered_units.append(unit)

        if i % 100 == 0 or i == len(units):
            print(f"  [{i}/{len(units)}] 规则={n_rule} LLM={n_llm} 跳过={n_skip}")
            _flush(tiered_units, OUT_TIERED)

    _flush(tiered_units, OUT_TIERED)

    # 统计
    tiers = Counter(u.get("kb_tier", 3) for u in tiered_units)
    stats = {
        "total": len(tiered_units),
        "L1_regulatory": tiers[1],
        "L2_parameter":  tiers[2],
        "L3_background": tiers[3],
        "L1_pct": round(tiers[1] / len(tiered_units) * 100, 1),
        "L2_pct": round(tiers[2] / len(tiered_units) * 100, 1),
        "L3_pct": round(tiers[3] / len(tiered_units) * 100, 1),
        "method": {"rule": n_rule, "llm": n_llm, "resume": n_skip},
        "by_source_type": _tier_by_source(tiered_units),
    }
    with open(OUT_STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # 导出 L1 单元供人工抽查
    l1_units = [u for u in tiered_units if u.get("kb_tier") == 1]
    _write_review_csv(l1_units, OUT_CSV)

    print("\n=== 分级完成 ===")
    print(f"L1 (监管层): {tiers[1]:4d} 条  ({stats['L1_pct']}%)")
    print(f"L2 (参数层): {tiers[2]:4d} 条  ({stats['L2_pct']}%)")
    print(f"L3 (背景层): {tiers[3]:4d} 条  ({stats['L3_pct']}%)")
    print(f"\n输出: {OUT_TIERED}")
    print(f"统计: {OUT_STATS}")
    print(f"L1抽查表: {OUT_CSV}")
    print("\n下一步:")
    print("  1. 检查 tier_review.csv 中的 L1 单元，确认分级正确")
    print("  2. 运行 python scripts/63_extract_ccs_units.py（需要CCS PDF）")
    print("  3. 运行 python scripts/64_apply_tiered_kb.py（重建带层级的索引）")


def _tier_by_source(units: list[dict]) -> dict:
    result: dict[str, dict[str, int]] = {}
    for u in units:
        src = u.get("metadata", {}).get("source_type", "unknown")
        tier = str(u.get("kb_tier", 3))
        if src not in result:
            result[src] = {"L1": 0, "L2": 0, "L3": 0}
        result[src][f"L{tier}"] = result[src].get(f"L{tier}", 0) + 1
    return result


def _flush(units: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")


def _write_review_csv(units: list[dict], path: Path) -> None:
    fields = ["id", "kb_tier", "tier_reason", "primary_component", "primary_intent",
              "source_type", "source_document", "text_snippet"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for u in units:
            meta = u.get("metadata", {})
            row = {
                "id": u.get("id", ""),
                "kb_tier": u.get("kb_tier", ""),
                "tier_reason": u.get("tier_reason", ""),
                "primary_component": u.get("primary_component", ""),
                "primary_intent": u.get("primary_intent", ""),
                "source_type": meta.get("source_type", ""),
                "source_document": meta.get("source_document", "")[:60],
                "text_snippet": u.get("text", "")[:200].replace("\n", " "),
            }
            w.writerow(row)


if __name__ == "__main__":
    main()
