# scripts/68_traceability_metrics.py
"""
可追溯性指标：RAG v3 vs no-RAG 的五项新指标。

指标列表：
  1. 无归因数字率   — 含数字 shall 中无 evidence_ids 的比例
  2. 条文引用率     — RAG shall 引用了有 constraint.规范依据 的 KB 单元的比例
  3. L1强制覆盖率   — 180条 L1强制 单元中被 RAG 检索到的比例
  4. 数字KB可溯率   — 含数字 shall 中数字值能在 KB 文本中找到依据的比例
  5. 证据层级质量   — RAG 引用的 evidence_ids 中属于 L1强制 层的比例

用法：
  python scripts/68_traceability_metrics.py

输出：
  data/search_results/exp_v3/traceability_metrics.json
  data/search_results/exp_v3/traceability_summary.txt
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

EXP  = PROJECT_ROOT / "data" / "search_results" / "exp_v3"
KB_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units_v2.jsonl"

# ---------------------------------------------------------------------------
# 数字抽取：匹配 "数值 + 工程单位"
# ---------------------------------------------------------------------------
NUMBER_RE = re.compile(
    r"(?<![a-zA-Z\d])"
    r"(\d+(?:[.,]\d+)?(?:\s*[–\-~～至到]\s*\d+(?:[.,]\d+)?)?)"   # 数值（含范围）
    r"\s*"
    r"(°C|℃|°F|MPa|kPa|Pa|bar|%|台|秒|分钟|小时|mm|cm|m[^s]|m³|"
    r"L/min|kW|MW|Hz|ppm|rpm|kN|m/s)",
    re.UNICODE,
)


def extract_numbers(text: str) -> list[str]:
    """返回 "值+单位" 字符串列表，去重。"""
    raw = NUMBER_RE.findall(text)
    # raw = [(数值, 单位), ...]；拼回字符串，保留首个数值（去范围后缀）
    result = []
    for val, unit in raw:
        # 取范围左侧数值
        base_val = re.split(r"[–\-~～至到]", val)[0].strip()
        token = f"{base_val}{unit}"
        if token not in result:
            result.append(token)
    return result


def _unit_full_text(u: dict) -> str:
    """拼接 KB 单元的可搜索文本。"""
    parts = [
        u.get("text", ""),
        u.get("search_text", ""),
    ]
    c = u.get("constraint") or {}
    parts.append(c.get("核心要求") or "")
    parts.append(c.get("可接受标准") or "")
    parts.append(c.get("规范依据") or "")
    meta = u.get("metadata") or {}
    parts.append(meta.get("normalized_summary") or "")
    return " ".join(filter(None, parts))


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def main() -> None:
    # ── 加载 KB ──────────────────────────────────────────────────────────────
    units: dict[str, dict] = {}
    for line in KB_PATH.open(encoding="utf-8"):
        u = json.loads(line)
        uid = u.get("id") or u.get("unit_id")
        if uid:
            units[uid] = u

    # 预计算：L1强制 集合
    l1_mandatory_ids: set[str] = {
        uid for uid, u in units.items()
        if u.get("kb_tier") == "L1"
        and (u.get("constraint") or {}).get("强制级别") == "强制"
    }
    print(f"KB 单元数: {len(units)}")
    print(f"L1强制 单元数: {len(l1_mandatory_ids)}")

    # 预计算：有 规范依据 的单元集合
    has_biaozhun: set[str] = {
        uid for uid, u in units.items()
        if (u.get("constraint") or {}).get("规范依据")
    }
    print(f"有 规范依据 的 KB 单元: {len(has_biaozhun)}")

    # 预计算：KB 全量文本（用于 no-RAG 数字可溯查找）
    kb_full_texts: list[tuple[str, str]] = [
        (uid, _unit_full_text(u)) for uid, u in units.items()
    ]
    # 预计算：KB 中出现的所有 "数值+单位" 字符串
    kb_number_tokens: set[str] = set()
    for _, txt in kb_full_texts:
        kb_number_tokens.update(extract_numbers(txt))
    print(f"KB 中唯一 数值+单位 token: {len(kb_number_tokens)}")

    # ── 加载实验结果 ─────────────────────────────────────────────────────────
    rag_data   = json.loads((EXP / "rag_v3_results.json").read_text(encoding="utf-8"))
    norag_data = json.loads((EXP / "norag_results.json").read_text(encoding="utf-8"))

    def iter_shalls(data):
        for rs in data["result_sets"]:
            sid = rs["source_requirement_id"]
            for er in rs.get("engineering_requirements", []):
                yield sid, er

    # ── 逐条计算 ─────────────────────────────────────────────────────────────

    # --- RAG ---
    rag_metrics: list[dict] = []
    all_rag_eids: set[str] = set()

    for sid, er in iter_shalls(rag_data):
        stmt    = er.get("shall_statement", "")
        eids    = er.get("evidence_ids") or []
        nums    = extract_numbers(stmt)
        has_num = bool(nums)

        # 1. 无归因数字率
        unsupported = has_num and len(eids) == 0

        # 2. 条文引用率
        cite_biaozhun = any(e in has_biaozhun for e in eids)

        # 3. L1强制命中（per-shall）
        cites_l1 = any(e in l1_mandatory_ids for e in eids)

        # 4a. 数字可溯率（cited evidence）
        if has_num and eids:
            cited_texts = " ".join(_unit_full_text(units[e]) for e in eids if e in units)
            cited_nums  = set(extract_numbers(cited_texts))
            grounded_in_cited = any(n in cited_nums for n in nums)
        elif has_num and not eids:
            grounded_in_cited = False
        else:
            grounded_in_cited = None  # no number → N/A

        # 5. 证据层级质量（per-shall）
        l1_frac = (sum(1 for e in eids if e in l1_mandatory_ids) / len(eids)
                   if eids else 0.0)

        all_rag_eids.update(eids)
        rag_metrics.append({
            "sid": sid,
            "stmt_preview": stmt[:60],
            "has_number": has_num,
            "n_numbers": len(nums),
            "n_evidence": len(eids),
            "unsupported_numeric": unsupported,
            "cite_biaozhun": cite_biaozhun,
            "cites_l1_mandatory": cites_l1,
            "numeric_grounded_in_cited": grounded_in_cited,
            "l1_evidence_fraction": l1_frac,
        })

    # --- no-RAG ---
    norag_metrics: list[dict] = []

    for sid, er in iter_shalls(norag_data):
        stmt    = er.get("shall_statement", "")
        eids    = er.get("evidence_ids") or []  # always []
        nums    = extract_numbers(stmt)
        has_num = bool(nums)

        unsupported = has_num  # all no-RAG shalls have no evidence

        # 数字 KB 可溯率（no-RAG：在全量 KB 中找）
        if has_num:
            grounded_in_kb = any(n in kb_number_tokens for n in nums)
        else:
            grounded_in_kb = None

        norag_metrics.append({
            "sid": sid,
            "stmt_preview": stmt[:60],
            "has_number": has_num,
            "n_numbers": len(nums),
            "n_evidence": 0,
            "unsupported_numeric": unsupported,
            "cite_biaozhun": False,
            "cites_l1_mandatory": False,
            "numeric_grounded_in_kb": grounded_in_kb,
        })

    # ── 汇总统计 ─────────────────────────────────────────────────────────────
    def pct(num, den):
        return (num / den * 100) if den else 0.0

    # RAG
    total_rag = len(rag_metrics)
    rag_numeric = [m for m in rag_metrics if m["has_number"]]
    rag_unsup   = [m for m in rag_numeric if m["unsupported_numeric"]]
    rag_cite_bz = [m for m in rag_metrics if m["cite_biaozhun"]]
    rag_cite_l1 = [m for m in rag_metrics if m["cites_l1_mandatory"]]
    rag_grounded = [m for m in rag_numeric if m["numeric_grounded_in_cited"] is True]

    # L1强制覆盖率（union）
    l1_covered = all_rag_eids & l1_mandatory_ids
    l1_coverage_pct = pct(len(l1_covered), len(l1_mandatory_ids))

    # 证据层级质量（只算有 evidence 的 shall）
    rag_with_ev = [m for m in rag_metrics if m["n_evidence"] > 0]
    avg_l1_frac = (sum(m["l1_evidence_fraction"] for m in rag_with_ev)
                   / len(rag_with_ev)) if rag_with_ev else 0.0

    # no-RAG
    total_norag = len(norag_metrics)
    norag_numeric = [m for m in norag_metrics if m["has_number"]]
    norag_grounded_kb = [m for m in norag_numeric if m["numeric_grounded_in_kb"] is True]

    summary = {
        "rag": {
            "total_shalls": total_rag,
            "numeric_shalls": len(rag_numeric),
            "numeric_rate_pct": pct(len(rag_numeric), total_rag),
            "unsupported_numeric_rate_pct": pct(len(rag_unsup), len(rag_numeric)),
            "clause_citation_rate_pct": pct(len(rag_cite_bz), total_rag),
            "l1_mandatory_shall_rate_pct": pct(len(rag_cite_l1), total_rag),
            "l1_mandatory_coverage_pct": l1_coverage_pct,
            "l1_mandatory_units_covered": len(l1_covered),
            "l1_mandatory_units_total": len(l1_mandatory_ids),
            "numeric_grounded_in_cited_pct": pct(len(rag_grounded), len(rag_numeric)),
            "avg_l1_evidence_fraction_pct": avg_l1_frac * 100,
        },
        "norag": {
            "total_shalls": total_norag,
            "numeric_shalls": len(norag_numeric),
            "numeric_rate_pct": pct(len(norag_numeric), total_norag),
            "unsupported_numeric_rate_pct": 100.0,
            "clause_citation_rate_pct": 0.0,
            "l1_mandatory_shall_rate_pct": 0.0,
            "l1_mandatory_coverage_pct": 0.0,
            # 下列值用于附录：no-RAG 数字偶然出现在 KB 的比例（非有意引用）
            "numeric_coincidental_kb_match_pct": pct(len(norag_grounded_kb), len(norag_numeric)),
        },
        "meta": {
            "kb_units_total": len(units),
            "l1_mandatory_total": len(l1_mandatory_ids),
            "kb_number_tokens": len(kb_number_tokens),
            "units_with_biaozhun": len(has_biaozhun),
        }
    }

    # ── 输出 ─────────────────────────────────────────────────────────────────
    out_json = EXP / "traceability_metrics.json"
    out_txt  = EXP / "traceability_summary.txt"

    with out_json.open("w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "rag_per_shall": rag_metrics,
            "norag_per_shall": norag_metrics,
            "l1_covered_ids": sorted(l1_covered),
        }, f, ensure_ascii=False, indent=2)

    lines = _fmt_summary(summary)
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    for ln in lines:
        print(ln)

    print(f"\n已写入: {out_json}")
    print(f"已写入: {out_txt}")


def _fmt_summary(s: dict) -> list[str]:
    r, n = s["rag"], s["norag"]
    m = s["meta"]
    lines = [
        "=" * 65,
        "可追溯性指标对比：RAG v3  vs  no-RAG",
        "=" * 65,
        "",
        f"{'指标':<32}  {'RAG v3':>10}  {'no-RAG':>10}",
        "-" * 58,
        f"{'shall 总数':<32}  {r['total_shalls']:>10}  {n['total_shalls']:>10}",
        f"{'含数字 shall 数（率）':<32}  "
        f"{r['numeric_shalls']:>5}({r['numeric_rate_pct']:4.1f}%)  "
        f"{n['numeric_shalls']:>5}({n['numeric_rate_pct']:4.1f}%)",
        "",
        "── 指标1：无归因数字率 (↓ better) ─────────────────────",
        f"  含数字且无 evidence_ids 的比例（数字无法追溯来源）",
        f"  {'RAG v3 :':20s} {r['unsupported_numeric_rate_pct']:6.1f}%",
        f"  {'no-RAG :':20s} {n['unsupported_numeric_rate_pct']:6.1f}%",
        f"  → no-RAG 所有含数字 shall ({n['numeric_shalls']}条) 均无任何规范依据",
        "",
        "── 指标2：条文引用率 (↑ better) ───────────────────────",
        f"  shall 中引用了 constraint.规范依据 非空的 KB 单元的比例",
        f"  {'RAG v3 :':20s} {r['clause_citation_rate_pct']:6.1f}%",
        f"  {'no-RAG :':20s} {n['clause_citation_rate_pct']:6.1f}%",
        f"  (KB 中有规范依据的单元共 {m.get('units_with_biaozhun', 'N/A')} 条)",
        "",
        "── 指标3：L1强制单元覆盖率 (↑ better) ─────────────────",
        f"  180 条 L1强制单元中被 RAG evidence 触及的比例",
        f"  {'RAG v3 :':20s} {r['l1_mandatory_coverage_pct']:6.1f}%  "
        f"({r['l1_mandatory_units_covered']}/{r['l1_mandatory_units_total']} 条)",
        f"  {'no-RAG :':20s} {n['l1_mandatory_coverage_pct']:6.1f}%",
        f"  RAG shall 中引用 L1强制 证据的比例: {r['l1_mandatory_shall_rate_pct']:.1f}%",
        "",
        "── 指标4：数字可溯性 (↑ better) ──────────────────────",
        f"  含数字 shall 中，数字值出现在所引用 KB 单元文本里的比例",
        f"  （衡量数字是否有具体来源支撑，非凭空生成）",
        f"  {'RAG v3 (cited匹配):':24s} {r['numeric_grounded_in_cited_pct']:6.1f}%",
        f"  {'no-RAG (无引用):':24s}      0.0%  [无任何 evidence_ids]",
        f"  附：no-RAG 数字偶然出现在全量 KB 中的率: "
        f"{n['numeric_coincidental_kb_match_pct']:.1f}%",
        f"  （偶然匹配≠有意引用；no-RAG 未使用 KB 生成上述数字）",
        "",
        "── 指标5：证据层级质量 (↑ better) ─────────────────────",
        f"  RAG 每条 shall 所引用证据中，L1强制 级别占比（均值）",
        f"  {'RAG v3 :':20s} {r['avg_l1_evidence_fraction_pct']:6.1f}%",
        f"  {'no-RAG :':20s}      N/A (无证据引用)",
        "",
        "=" * 65,
        f"  KB: {m['kb_units_total']} 单元  |  L1强制: {m['l1_mandatory_total']} 条  |"
        f"  KB数字token: {m['kb_number_tokens']}",
        "=" * 65,
    ]
    return lines


if __name__ == "__main__":
    main()
