"""
Phase 4: 基于分层KB的合规可追溯性指标评估。

三个新指标（no-RAG 在架构上得 0 分）：
  1. 规范覆盖率 (Regulatory Coverage Rate, RCR)
     = 含≥1个L1证据引用的shall数 / shall总数
     no-RAG: 0%（无证据引用）

  2. 合规完整性 (Compliance Completeness, CC)
     = 被至少1个shall引用的不重复L1单元数 / KB中L1总单元数
     no-RAG: 0%（无证据引用）

  3. 审查就绪度 (Review Readiness, RR)
     = 含≥1个L1直接引用(evidence_strength=direct)的shall数 / shall总数
     no-RAG: 0%（无法追溯到规范条文）

前置条件:
  - 已完成 Phase 3（运行 62_tier_kb_units.py，产生 evidence_units_tiered.jsonl）
  - 已有 RAG v3 实验结果（data/search_results/exp_v3/rag_v3_results.json）

用法:
  python scripts/64_compliance_metrics.py
  python scripts/64_compliance_metrics.py --rag-file path/to/results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA         = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR  = PROJECT_ROOT / "data" / "search_results"
TIERED_UNITS = DATA / "evidence_units_tiered.jsonl"
UNITS_PATH   = DATA / "evidence_units.jsonl"  # 备用

RAG_RESULTS  = RESULTS_DIR / "exp_v3" / "rag_v3_results.json"
NORAG_RESULTS= RESULTS_DIR / "exp_v3" / "norag_results.json"
OUT_REPORT   = RESULTS_DIR / "compliance_metrics.json"


def _load_l1_unit_ids(tiered_path: Path, fallback_path: Path) -> set[str]:
    """加载所有 kb_tier=1 的单元ID"""
    path = tiered_path if tiered_path.exists() else fallback_path
    if not path.exists():
        print(f"⚠ 找不到KB文件: {path}")
        return set()
    l1_ids = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u.get("kb_tier") == 1:
                l1_ids.add(u["id"])
            # 兼容：ship_rule 类型也视为L1
            elif u.get("metadata", {}).get("source_type") in ("ship_rule", "class_rule"):
                l1_ids.add(u["id"])
    return l1_ids


def _load_l1_direct_ids(tiered_path: Path, fallback_path: Path) -> set[str]:
    """加载 kb_tier=1 且 evidence_strength=direct 的单元ID"""
    path = tiered_path if tiered_path.exists() else fallback_path
    if not path.exists():
        return set()
    ids = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            meta = u.get("metadata", {})
            is_l1 = u.get("kb_tier") == 1 or meta.get("source_type") in ("ship_rule", "class_rule")
            is_direct = meta.get("evidence_strength") == "direct"
            if is_l1 and is_direct:
                ids.add(u["id"])
    return ids


def _extract_shalls_from_results(results_path: Path) -> list[dict]:
    """从实验结果文件提取所有shall及其证据引用"""
    if not results_path.exists():
        return []
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)

    shalls = []

    # 格式1: {"result_sets": [...]} (v3 格式)
    if isinstance(data, dict) and "result_sets" in data:
        for rs in data["result_sets"]:
            src_id = rs.get("source_requirement_id", "")
            for er in rs.get("engineering_requirements", []):
                refs = er.get("evidence_refs", er.get("evidence_ids", []))
                shalls.append({
                    "source_id": src_id,
                    "shall": er.get("shall_statement", ""),
                    "evidence_refs": refs if isinstance(refs, list) else [],
                })
        return shalls

    # 格式2: [{"source_requirement_id": ..., "engineering_requirements": [...]}]
    items = data if isinstance(data, list) else data.get("results", data.get("requirements", []))
    for item in items:
        src_id = item.get("source_requirement_id", item.get("id", ""))
        for er in item.get("engineering_requirements", []):
            refs = er.get("evidence_refs", er.get("evidence_ids", []))
            shalls.append({
                "source_id": src_id,
                "shall": er.get("shall_statement", ""),
                "evidence_refs": refs if isinstance(refs, list) else [],
            })
        if "shall_statement" in item:
            refs = item.get("evidence_refs", item.get("evidence_ids", []))
            shalls.append({
                "source_id": src_id,
                "shall": item.get("shall_statement", ""),
                "evidence_refs": refs if isinstance(refs, list) else [],
            })

    return shalls


def _compute_metrics(shalls: list[dict], l1_ids: set[str], l1_direct_ids: set[str], label: str) -> dict:
    """计算三个合规指标"""
    if not shalls:
        return {
            "label": label, "n_shalls": 0,
            "RCR": 0.0, "CC": 0.0, "RR": 0.0,
            "covered_l1_units": 0,
            "total_l1_units": len(l1_ids),
        }

    rcr_count = 0   # 含>=1个L1引用
    rr_count  = 0   # 含>=1个L1直接引用
    cited_l1  = set()  # 被引用的L1单元

    for shall in shalls:
        refs = shall.get("evidence_refs", [])
        refs_l1        = [r for r in refs if r in l1_ids]
        refs_l1_direct = [r for r in refs if r in l1_direct_ids]

        if refs_l1:
            rcr_count += 1
            cited_l1.update(refs_l1)
        if refs_l1_direct:
            rr_count += 1

    n = len(shalls)
    total_l1 = len(l1_ids) if l1_ids else 1  # 避免除以零

    return {
        "label": label,
        "n_shalls": n,
        "RCR": round(rcr_count / n, 4),          # 规范覆盖率
        "CC":  round(len(cited_l1) / total_l1, 4),  # 合规完整性
        "RR":  round(rr_count / n, 4),             # 审查就绪度
        "covered_l1_units": len(cited_l1),
        "total_l1_units": len(l1_ids),
        "detail": {
            "shalls_with_l1_citation": rcr_count,
            "shalls_with_l1_direct":   rr_count,
            "shalls_no_citation":      sum(1 for s in shalls if not s["evidence_refs"]),
        }
    }


def _per_requirement_breakdown(shalls: list[dict], l1_ids: set[str]) -> dict[str, dict]:
    """按源需求分组统计覆盖情况"""
    groups: dict[str, list] = defaultdict(list)
    for s in shalls:
        groups[s["source_id"]].append(s)

    breakdown = {}
    for src_id, group in groups.items():
        n = len(group)
        l1_covered = sum(1 for s in group if any(r in l1_ids for r in s["evidence_refs"]))
        breakdown[src_id] = {
            "n_shalls": n,
            "l1_covered": l1_covered,
            "rcr": round(l1_covered / n, 3) if n else 0,
        }
    return breakdown


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rag-file",   default=str(RAG_RESULTS),   help="RAG结果文件路径")
    ap.add_argument("--norag-file", default=str(NORAG_RESULTS), help="no-RAG结果文件路径")
    args = ap.parse_args()

    # 加载KB层级信息
    l1_ids        = _load_l1_unit_ids(TIERED_UNITS, UNITS_PATH)
    l1_direct_ids = _load_l1_direct_ids(TIERED_UNITS, UNITS_PATH)
    print(f"KB层级: L1单元={len(l1_ids)}个 (其中direct={len(l1_direct_ids)}个)")

    if not l1_ids:
        print("\n⚠ 未找到L1单元！请先运行:")
        print("  python scripts/62_tier_kb_units.py")
        print("  或确认 CCS 规范单元已加入 evidence_units_tiered.jsonl")

    # 加载实验结果
    rag_path   = Path(args.rag_file)
    norag_path = Path(args.norag_file)

    rag_shalls   = _extract_shalls_from_results(rag_path)
    norag_shalls = _extract_shalls_from_results(norag_path)

    print(f"\n实验结果:")
    print(f"  RAG v3:  {len(rag_shalls)} 个shall  (来自 {rag_path.name})")
    print(f"  no-RAG:  {len(norag_shalls)} 个shall  (来自 {norag_path.name})")

    if not rag_shalls and not norag_shalls:
        print("\n⚠ 未找到实验结果，请确认文件路径。")
        print(f"  预期RAG结果: {RAG_RESULTS}")
        print(f"  预期no-RAG结果: {NORAG_RESULTS}")
        return

    # 计算指标
    rag_metrics   = _compute_metrics(rag_shalls,   l1_ids, l1_direct_ids, "RAG_v3")
    norag_metrics = _compute_metrics(norag_shalls, l1_ids, l1_direct_ids, "no_RAG")

    # 输出报告
    report = {
        "summary": {
            "metric_description": {
                "RCR": "规范覆盖率 = shalls中含≥1个L1证据引用的比例 (no-RAG永远0%)",
                "CC":  "合规完整性 = KB中L1单元被引用的比例 (no-RAG永远0%)",
                "RR":  "审查就绪度 = shalls中含≥1个L1直接引用的比例 (no-RAG永远0%)",
            },
            "RAG_v3":  {"RCR": rag_metrics["RCR"],   "CC": rag_metrics["CC"],   "RR": rag_metrics["RR"]},
            "no_RAG":  {"RCR": norag_metrics["RCR"], "CC": norag_metrics["CC"], "RR": norag_metrics["RR"]},
        },
        "detail": {
            "RAG_v3": rag_metrics,
            "no_RAG": norag_metrics,
        },
        "per_requirement": {
            "RAG_v3": _per_requirement_breakdown(rag_shalls, l1_ids),
        },
    }

    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 打印汇总
    print("\n" + "=" * 55)
    print(f"{'指标':<20} {'RAG v3':>12} {'no-RAG':>12}")
    print("-" * 55)
    for metric, name in [("RCR","规范覆盖率"), ("CC","合规完整性"), ("RR","审查就绪度")]:
        rv = f"{rag_metrics[metric]*100:.1f}%"
        nv = f"{norag_metrics[metric]*100:.1f}%"
        print(f"{name:<18} ({metric}) {rv:>12} {nv:>12}")
    print("=" * 55)
    print(f"\n详细报告: {OUT_REPORT}")

    # 提示下一步
    if rag_metrics["RCR"] == 0:
        print("\n⚠ RAG RCR=0: KB中L1单元尚未被引用。")
        print("  可能原因: 1) KB分级未完成  2) CCS规范单元未加入KB")
        print("  建议: 完成Phase 1-3后重新运行")


if __name__ == "__main__":
    main()
