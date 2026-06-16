# scripts/76_ablation_verify.py
"""
消融实验 KB 数值核查与对比汇总。

读取 4 个臂的结果（filtered_rrf 复用 exp_v3/rag_v3_results.json，
其余从 ablation/ 目录读取），对每条含数字 shall 做 DeepSeek 数值核查，
汇总输出对比表格。

输出：
  data/search_results/ablation/ablation_verification.json
  data/search_results/ablation/ablation_summary.txt

用法：
  python scripts/76_ablation_verify.py --limit 5   # 冒烟（每臂只核查前5条含数字shall）
  python scripts/76_ablation_verify.py             # 全量
  python scripts/76_ablation_verify.py --arms filtered_rrf nofilter_rrf  # 指定臂
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.text_utils import simple_tokens

EXP_V3  = PROJECT_ROOT / "data" / "search_results" / "exp_v3"
ABL_DIR = PROJECT_ROOT / "data" / "search_results" / "ablation"
IDX_DIR = PROJECT_ROOT / "data" / "indexes" / "evidence_units"
KB_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units_v2.jsonl"

ALL_ARMS = ["filtered_rrf", "nofilter_rrf", "filtered_bm25", "filtered_vec"]

ARM_LABELS = {
    "filtered_rrf":  "Filter+RRF (v3基线)",
    "nofilter_rrf":  "NoFilter+RRF",
    "filtered_bm25": "Filter+BM25only",
    "filtered_vec":  "Filter+Veconly",
}


# ── 复用 script 70 的核查工具函数 ─────────────────────────────────────────────

NUMBER_RE = re.compile(
    r"(?<![a-zA-Z\d])"
    r"(\d+(?:[.,]\d+)?(?:\s*[–\-~～至到]\s*\d+(?:[.,]\d+)?)?)"
    r"\s*"
    r"(°C|℃|°F|MPa|kPa|Pa|bar|%|台|秒|分钟|小时|mm|cm|m³|"
    r"L/min|kW|MW|Hz|ppm|rpm|kN|m/s)",
    re.UNICODE,
)

VERDICT_RE = re.compile(r"(SUPPORTED|CONTRADICTED|UNVERIFIABLE)", re.IGNORECASE)

VERIFY_SYS = "你是船舶工程规范核查专家，逻辑严谨、回答简洁。"
VERIFY_TMPL = """\
【工程需求陈述】
{shall}

【检索到的知识库证据（共{n}条）】
{evidence}

【任务】
逐一判断上述工程需求中每一个含单位的具体数值（如 10秒、±2°C、100%容量）是否与证据一致。

对每个数值，从以下三类中选一：
  SUPPORTED    — 证据明确支持该数值或包含该数值范围
  CONTRADICTED — 证据针对同一参数明确给出了不同数值
  UNVERIFIABLE — 证据未涉及该具体数值参数

输出格式（每个数值占一行，无需额外说明）：
<数值> | <SUPPORTED/CONTRADICTED/UNVERIFIABLE> | <一句中文理由>

若需求中无含单位的具体数值，输出一行：NO_NUMERIC_CLAIMS"""


def has_numbers(text: str) -> bool:
    return bool(NUMBER_RE.search(text))


def extract_number_tokens(text: str) -> list[str]:
    seen, out = set(), []
    for val, unit in NUMBER_RE.findall(text):
        base = re.split(r"[–\-~～至到]", val)[0].strip()
        token = f"{base}{unit}"
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


def fmt_unit(u: dict) -> str:
    parts = [f"[{u.get('id','?')}] {u.get('search_text','')}"]
    text = u.get("text", "")
    if text:
        parts.append(text[:400])
    c = u.get("constraint") or {}
    if c.get("核心要求"):  parts.append(f"核心要求: {c['核心要求']}")
    if c.get("可接受标准"): parts.append(f"可接受标准: {c['可接受标准']}")
    return "\n".join(parts)


def bm25_search_posthoc(query: str, bm25, records: list[dict], top_k: int = 5) -> list[dict]:
    qtoks  = simple_tokens(query)
    scores = bm25.get_scores(qtoks)
    top_idx = np.argsort(scores)[-top_k:][::-1]
    return [{"unit": records[i], "bm25_score": float(scores[i])}
            for i in top_idx if scores[i] > 0]


def call_deepseek(shall: str, units: list[dict], client, model: str) -> str:
    evidence_str = "\n\n---\n".join(fmt_unit(u) for u in units)
    prompt = VERIFY_TMPL.format(shall=shall, n=len(units), evidence=evidence_str)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": VERIFY_SYS},
                  {"role": "user",   "content": prompt}],
        temperature=0, max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


def parse_verdicts(llm_out: str) -> dict:
    result = {"supported": [], "contradicted": [], "unverifiable": []}
    if "NO_NUMERIC_CLAIMS" in llm_out.upper():
        return result
    for line in llm_out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        m = VERDICT_RE.search(line)
        if not m:
            continue
        verdict = m.group(1).upper()
        if verdict == "SUPPORTED":
            result["supported"].append(line)
        elif verdict == "CONTRADICTED":
            result["contradicted"].append(line)
        else:
            result["unverifiable"].append(line)
    return result


def classify_shall(verdicts: dict) -> str:
    if verdicts["contradicted"]: return "conflict"
    if verdicts["supported"]:    return "supported"
    if verdicts["unverifiable"]: return "unverifiable"
    return "no_numeric"


# ── 加载各臂结果 ──────────────────────────────────────────────────────────────

def load_arm_data(arm: str) -> dict | None:
    if arm == "filtered_rrf":
        path = EXP_V3 / "rag_v3_results.json"
    else:
        path = ABL_DIR / f"{arm}_results.json"
    if not path.exists():
        print(f"  [跳过] {arm}: 文件不存在 ({path})")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def collect_numeric_rows(data: dict, arm: str) -> list[dict]:
    rows = []
    for rs in data["result_sets"]:
        sid = rs["source_requirement_id"]
        for er in rs.get("engineering_requirements", []):
            stmt = er.get("shall_statement", "")
            if has_numbers(stmt):
                rows.append({
                    "arm":          arm,
                    "sid":          sid,
                    "stmt":         stmt,
                    "evidence_ids": er.get("evidence_ids") or [],
                    "numbers":      extract_number_tokens(stmt),
                })
    return rows


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",  type=int, default=0, help="每臂只取前N条含数字shall（冒烟）")
    ap.add_argument("--arms",   nargs="+", choices=ALL_ARMS, default=ALL_ARMS)
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # 加载 BM25（用于 nofilter_rrf/filtered_bm25/filtered_vec 的 post-hoc 验证，
    # 但实际上这些臂的 shall 都有 evidence_ids，可直接用 cited）
    print("加载 BM25 索引...")
    bm25      = pickle.load((IDX_DIR / "bm25.pkl").open("rb"))
    idx_recs  = pickle.load((IDX_DIR / "records.pkl").open("rb"))
    kb_units: dict[str, dict] = {}
    for line in KB_PATH.open(encoding="utf-8"):
        u = json.loads(line)
        kb_units[u["id"]] = u
    full_recs = [kb_units.get(r["id"], r) for r in idx_recs]
    print(f"  BM25: {len(idx_recs)} 条  KB: {len(kb_units)} 条")

    ABL_DIR.mkdir(parents=True, exist_ok=True)

    # 收集所有待核查行
    all_rows: list[dict] = []
    for arm in args.arms:
        data = load_arm_data(arm)
        if data is None:
            continue
        rows = collect_numeric_rows(data, arm)
        if args.limit:
            rows = rows[:args.limit]
        print(f"  {arm}: {len(rows)} 条含数字shall 待核查")
        all_rows.extend(rows)

    total = len(all_rows)
    print(f"\n共 {total} 条 shall 待核查\n")

    results: list[dict] = []
    for done, row in enumerate(all_rows, 1):
        arm  = row["arm"]
        stmt = row["stmt"]

        # 所有 RAG 臂都有 cited evidence_ids，直接用；fallback 到 BM25 posthoc
        eids  = row["evidence_ids"]
        units = [kb_units[e] for e in eids if e in kb_units][:5]
        retrieval = "cited"
        if not units:
            hits  = bm25_search_posthoc(stmt, bm25, full_recs, top_k=5)
            units = [h["unit"] for h in hits]
            retrieval = "bm25_posthoc"

        if not units:
            label    = "unverifiable"
            verdicts = {"supported": [], "contradicted": [], "unverifiable": [], "raw": "NO_EVIDENCE"}
        else:
            try:
                raw      = call_deepseek(stmt, units, client, model)
                verdicts = parse_verdicts(raw)
                verdicts["raw"] = raw
                label    = classify_shall(verdicts)
            except Exception as exc:
                verdicts = {"supported": [], "contradicted": [], "unverifiable": [], "raw": f"ERROR:{exc}"}
                label    = "error"

        pct_done = done / total * 100
        print(f"  [{done:3d}/{total}]({pct_done:4.0f}%) {arm:18s} | {label:14s} | {stmt[:50]}")
        if verdicts.get("contradicted"):
            for c in verdicts["contradicted"]:
                print(f"    !! CONTRADICTED: {c[:80]}")

        time.sleep(0.3)
        results.append({
            "arm":          arm,
            "sid":          row["sid"],
            "stmt":         stmt,
            "numbers":      row["numbers"],
            "evidence_ids": row["evidence_ids"],
            "retrieval":    retrieval,
            "n_units":      len(units),
            "label":        label,
            "verdicts":     {k: v for k, v in verdicts.items() if k != "raw"},
            "llm_raw":      verdicts.get("raw", ""),
        })

    # 保存原始结果
    out_json = ABL_DIR / "ablation_verification.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)
    print(f"\n已写入: {out_json}")

    # 统计汇总
    summary_lines = _make_summary(results, args.arms)
    out_txt = ABL_DIR / "ablation_summary.txt"
    out_txt.write_text("\n".join(summary_lines), encoding="utf-8")
    print("\n".join(summary_lines))
    print(f"\n已写入: {out_txt}")


def _make_summary(results: list[dict], arms: list[str]) -> list[str]:
    def pct(n, d):
        return f"{n/d*100:5.1f}%" if d else "   N/A"

    lines = [
        "=" * 72,
        "消融实验 KB 数值核查汇总",
        "=" * 72,
        "",
        f"{'臂':<22} {'含数字shall':>8} {'SUPPORTED↑':>12} {'CONFLICT↓':>10} {'UNVERIF':>9}",
        "-" * 72,
    ]

    arm_stats: dict[str, dict] = {}
    for arm in arms:
        arm_rows = [r for r in results if r["arm"] == arm]
        if not arm_rows:
            continue
        n    = len(arm_rows)
        sup  = sum(1 for r in arm_rows if r["label"] == "supported")
        con  = sum(1 for r in arm_rows if r["label"] == "conflict")
        unv  = sum(1 for r in arm_rows if r["label"] == "unverifiable")
        arm_stats[arm] = {"n": n, "sup": sup, "con": con, "unv": unv}
        label = ARM_LABELS.get(arm, arm)
        lines.append(
            f"{label:<22} {n:>8d}  {pct(sup,n):>10}  {pct(con,n):>8}  {pct(unv,n):>8}"
        )

    lines += [
        "-" * 72,
        "",
        "说明：",
        "  SUPPORTED  = 引用证据明确支持该数值（↑ 越高越好）",
        "  CONFLICT   = 引用证据对同一参数给出不同数值（↓ 越低越好，幻觉指标）",
        "  UNVERIF    = 引用证据未涉及该参数（↓ 越低越好）",
        "  所有 RAG 臂均使用 cited evidence_ids 核查（非 BM25 post-hoc）",
        "=" * 72,
    ]

    # 增量对比：相对 filtered_rrf 基线
    if "filtered_rrf" in arm_stats and len(arm_stats) > 1:
        base = arm_stats["filtered_rrf"]
        lines += ["", "相对 Filter+RRF 基线的变化：", "-" * 50]
        for arm, st in arm_stats.items():
            if arm == "filtered_rrf":
                continue
            label = ARM_LABELS.get(arm, arm)
            d_sup = st["sup"] / st["n"] * 100 - base["sup"] / base["n"] * 100 if base["n"] else 0
            d_con = st["con"] / st["n"] * 100 - base["con"] / base["n"] * 100 if base["n"] else 0
            lines.append(
                f"  {label:<22}  SUPPORTED {d_sup:+.1f}pp  CONFLICT {d_con:+.1f}pp"
            )
        lines.append("=" * 72)

    return lines


if __name__ == "__main__":
    main()
