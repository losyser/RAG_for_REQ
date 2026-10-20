# scripts/70_norag_kb_verification.py
"""
Post-hoc KB 数值核查：no-RAG shall 的数值是否与 KB 一致？

核心逻辑：
  no-RAG arm:
    含数字 shall → BM25 检索 top-5 KB 单元 → DeepSeek 判断:
      SUPPORTED   = KB 明确支持该数值
      CONTRADICTED= KB 针对同一参数给出不同数值  ← 真正的幻觉证据
      UNVERIFIABLE= KB 未涉及该参数

  RAG arm:
    含数字 shall → 直接取 cited evidence_ids 对应的 KB 单元 → 同样的 DeepSeek 判断

  对比两组分布，重点看 CONTRADICTED 率。

用法：
  python scripts/70_norag_kb_verification.py [--limit N]   # limit 只跑前N条（冒烟）

输出：
  data/search_results/exp_v3/norag_kb_verification.json
  data/search_results/exp_v3/norag_kb_verification_summary.txt
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

EXP     = PROJECT_ROOT / "data" / "search_results" / "exp_v4"
IDX_DIR = PROJECT_ROOT / "data" / "indexes" / "evidence_units"
KB_PATH = PROJECT_ROOT / "data" / "processed" / "evidence_units_v3_audited.jsonl"

# ── 数字抽取（同 script 68）────────────────────────────────────────────────
NUMBER_RE = re.compile(
    r"(?<![a-zA-Z\d])"
    r"(\d+(?:[.,]\d+)?(?:\s*[–\-~～至到]\s*\d+(?:[.,]\d+)?)?)"
    r"\s*"
    r"(°C|℃|°F|MPa|kPa|Pa|bar|%|台|秒|分钟|小时|mm|cm|m³|"
    r"L/min|kW|MW|Hz|ppm|rpm|kN|m/s)",
    re.UNICODE,
)


def has_numbers(text: str) -> bool:
    return bool(NUMBER_RE.search(text))


def extract_number_tokens(text: str) -> list[str]:
    """返回 ['10秒', '±2°C', ...] 去重列表。"""
    seen, out = set(), []
    for val, unit in NUMBER_RE.findall(text):
        base = re.split(r"[–\-~～至到]", val)[0].strip()
        token = f"{base}{unit}"
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


# ── BM25 搜索 ────────────────────────────────────────────────────────────────

def bm25_search(query: str, bm25, records: list[dict], top_k: int = 5) -> list[dict]:
    qtoks  = simple_tokens(query)
    scores = bm25.get_scores(qtoks)
    top_idx = np.argsort(scores)[-top_k:][::-1]
    results = []
    for i in top_idx:
        if scores[i] > 0:
            results.append({"unit": records[i], "bm25_score": float(scores[i])})
    return results


def fmt_unit(u: dict) -> str:
    """把 KB 单元压缩成 LLM prompt 里的文本段。"""
    parts = [f"[{u.get('id','?')}] {u.get('search_text','')}"]
    text = u.get("text", "")
    if text:
        parts.append(text[:400])
    c = u.get("constraint") or {}
    core = c.get("核心要求", "")
    std  = c.get("可接受标准", "")
    if core: parts.append(f"核心要求: {core}")
    if std:  parts.append(f"可接受标准: {std}")
    return "\n".join(parts)


# ── DeepSeek 判断 ─────────────────────────────────────────────────────────────

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


def call_deepseek(shall: str, units: list[dict], client, model: str) -> str:
    evidence_str = "\n\n---\n".join(fmt_unit(u) for u in units)
    prompt = VERIFY_TMPL.format(
        shall=shall,
        n=len(units),
        evidence=evidence_str,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",  "content": VERIFY_SYS},
            {"role": "user",    "content": prompt},
        ],
        temperature=0,
        max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


# ── 解析 LLM 回复 ─────────────────────────────────────────────────────────────

VERDICT_RE = re.compile(r"(SUPPORTED|CONTRADICTED|UNVERIFIABLE)", re.IGNORECASE)


def parse_verdicts(llm_out: str) -> dict:
    """
    返回 {"supported": [...], "contradicted": [...], "unverifiable": [...]}
    每个列表里放对应的 "数值 | 理由" 字符串。
    """
    result = {"supported": [], "contradicted": [], "unverifiable": []}
    if "NO_NUMERIC_CLAIMS" in llm_out.upper():
        return result
    for line in llm_out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        m = re.fullmatch(r"(SUPPORTED|CONTRADICTED|UNVERIFIABLE)", line.split("|")[1].strip(), re.IGNORECASE)
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
    """
    综合所有数值的判断给 shall 打一个标签：
      conflict     — 至少一个数值 CONTRADICTED
      supported    — 历史 v1：至少一个数值 SUPPORTED（无冲突），不保证全部支持
      unverifiable — 无冲突，但无法验证
      no_numeric   — 无含单位数值
    """
    if verdicts["contradicted"]:
        return "conflict"
    if verdicts["supported"]:
        return "supported"
    if verdicts["unverifiable"]:
        return "unverifiable"
    return "no_numeric"


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前N条含数字shall（冒烟用）")
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # ── 加载 BM25 索引 ────────────────────────────────────────────────────────
    print("加载 BM25 索引...")
    bm25    = pickle.load((IDX_DIR / "bm25.pkl").open("rb"))
    idx_recs = pickle.load((IDX_DIR / "records.pkl").open("rb"))
    # id → full KB unit（含 constraint 等字段）
    kb_units: dict[str, dict] = {}
    for line in KB_PATH.open(encoding="utf-8"):
        u = json.loads(line)
        kb_units[u["id"]] = u
    # idx_recs 里的 unit 可能只有部分字段；用 kb_units 补全
    full_recs = [kb_units.get(r["id"], r) for r in idx_recs]
    print(f"  BM25 索引: {len(idx_recs)} 条  |  KB 单元: {len(kb_units)} 条")

    # ── 加载实验结果 ──────────────────────────────────────────────────────────
    rag_data   = json.loads((EXP / "rag_v4_results.json").read_text(encoding="utf-8"))
    norag_data = json.loads((EXP / "norag_v4_results.json").read_text(encoding="utf-8"))

    # ── 提取含数字 shall ───────────────────────────────────────────────────────
    # v4 schema: 数值位于 measurable_criterion；被引单元 ID 位于 evidence_citations[].kb_id
    def collect_numeric(data, arm_tag):
        rows = []
        for rs in data["result_sets"]:
            sid = rs["source_requirement_id"]
            for er in rs.get("engineering_requirements", []):
                shall     = er.get("shall_statement", "")
                criterion = er.get("measurable_criterion", "") or ""
                text      = f"{shall}（测量判据：{criterion}）" if criterion else shall
                if has_numbers(text):
                    eids = [c.get("kb_id") for c in (er.get("evidence_citations") or [])
                            if c.get("kb_id")]
                    rows.append({
                        "arm":        arm_tag,
                        "sid":        sid,
                        "stmt":       text,
                        "evidence_ids": eids,
                        "numbers":    extract_number_tokens(text),
                    })
        return rows

    rag_numeric   = collect_numeric(rag_data,   "rag_v3")
    norag_numeric = collect_numeric(norag_data, "no_rag")
    print(f"含数字 shall — RAG: {len(rag_numeric)}  no-RAG: {len(norag_numeric)}")

    if args.limit:
        rag_numeric   = rag_numeric[:args.limit]
        norag_numeric = norag_numeric[:args.limit]
        print(f"（冒烟模式：各取前 {args.limit} 条）")

    total = len(rag_numeric) + len(norag_numeric)
    results = []
    done = 0

    def process(row: dict) -> dict:
        nonlocal done
        done += 1
        stmt = row["stmt"]
        arm  = row["arm"]

        # 取证据单元
        if arm == "rag_v3":
            # RAG: 直接用 cited evidence_ids
            eids  = row["evidence_ids"]
            units = [kb_units[e] for e in eids if e in kb_units][:5]
            retrieval = "cited"
        else:
            # no-RAG: BM25 post-hoc 检索
            hits  = bm25_search(stmt, bm25, full_recs, top_k=5)
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
                verdicts = {"supported": [], "contradicted": [], "unverifiable": [],
                            "raw": f"ERROR: {exc}"}
                label    = "error"

        print(f"  [{done:3d}/{total}] {arm:8s} | {label:14s} | {stmt[:55]}")
        if verdicts.get("contradicted"):
            for c in verdicts["contradicted"]:
                print(f"    !! CONTRADICTED: {c[:80]}")

        time.sleep(0.3)
        return {
            "arm":        arm,
            "sid":        row["sid"],
            "stmt":       stmt,
            "numbers":    row["numbers"],
            "evidence_ids": row["evidence_ids"],
            "retrieval":  retrieval,
            "n_units":    len(units),
            "label":      label,
            "verdicts":   {k: v for k, v in verdicts.items() if k != "raw"},
            "llm_raw":    verdicts.get("raw", ""),
        }

    print("\n── RAG arm ────────────────────────────────────────────────────")
    for row in rag_numeric:
        results.append(process(row))

    print("\n── no-RAG arm ─────────────────────────────────────────────────")
    for row in norag_numeric:
        results.append(process(row))

    # ── 统计 ─────────────────────────────────────────────────────────────────
    def pct(n, d):
        return n / d * 100 if d else 0.0

    def stats(arm_tag):
        arm_rows = [r for r in results if r["arm"] == arm_tag]
        total_n  = len(arm_rows)
        by_label = {l: sum(1 for r in arm_rows if r["label"] == l)
                    for l in ("supported", "conflict", "unverifiable", "no_numeric", "error")}
        # per-number stats
        n_sup = sum(len(r["verdicts"].get("supported",   [])) for r in arm_rows)
        n_con = sum(len(r["verdicts"].get("contradicted", [])) for r in arm_rows)
        n_unv = sum(len(r["verdicts"].get("unverifiable", [])) for r in arm_rows)
        n_total = n_sup + n_con + n_unv
        return {
            "total_shalls":      total_n,
            "label_supported":   by_label["supported"],
            "label_conflict":    by_label["conflict"],
            "label_unverifiable":by_label["unverifiable"],
            "pct_supported":     pct(by_label["supported"],    total_n),
            "pct_conflict":      pct(by_label["conflict"],     total_n),
            "pct_unverifiable":  pct(by_label["unverifiable"], total_n),
            "num_supported":     n_sup,
            "num_contradicted":  n_con,
            "num_unverifiable":  n_unv,
            "num_pct_supported": pct(n_sup, n_total),
            "num_pct_contradicted": pct(n_con, n_total),
        }

    summary = {
        "rag_v3": stats("rag_v3"),
        "no_rag": stats("no_rag"),
    }

    # ── 写入 ──────────────────────────────────────────────────────────────────
    out_json = EXP / "norag_kb_verification.json"
    out_txt  = EXP / "norag_kb_verification_summary.txt"

    with out_json.open("w", encoding="utf-8") as f:
        json.dump({"summary": summary, "details": results}, f,
                  ensure_ascii=False, indent=2)

    lines = _fmt_summary(summary)
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    for ln in lines:
        print(ln)

    print(f"\n已写入: {out_json}")
    print(f"已写入: {out_txt}")

    # 打印冲突案例清单
    conflicts = [r for r in results if r["label"] == "conflict"]
    if conflicts:
        print(f"\n── CONTRADICTED 案例（{len(conflicts)} 条）────────────────────────")
        for r in conflicts:
            print(f"\n  [{r['arm']}] {r['sid']}  {r['stmt'][:80]}")
            for c in r["verdicts"].get("contradicted", []):
                print(f"    >> {c}")


def _fmt_summary(s: dict) -> list[str]:
    r = s.get("rag_v3", {})
    n = s.get("no_rag",  {})
    lines = [
        "",
        "=" * 68,
        "Post-hoc KB 数值核查结果：RAG v3  vs  no-RAG",
        "=" * 68,
        "",
        "【shall 级别分类】",
        f"{'标签':<18} {'RAG v3':>18} {'no-RAG':>18}",
        "-" * 58,
        f"{'含数字 shall 总数':<18}"
        f"  {r.get('total_shalls',0):>8}"
        f"  {n.get('total_shalls',0):>16}",
        f"{'SUPPORTED ↑':<18}"
        f"  {r.get('label_supported',0):>4} ({r.get('pct_supported',0):5.1f}%)"
        f"  {n.get('label_supported',0):>4} ({n.get('pct_supported',0):5.1f}%)",
        f"{'CONFLICT ↓':<18}"
        f"  {r.get('label_conflict',0):>4} ({r.get('pct_conflict',0):5.1f}%)"
        f"  {n.get('label_conflict',0):>4} ({n.get('pct_conflict',0):5.1f}%)",
        f"{'UNVERIFIABLE':<18}"
        f"  {r.get('label_unverifiable',0):>4} ({r.get('pct_unverifiable',0):5.1f}%)"
        f"  {n.get('label_unverifiable',0):>4} ({n.get('pct_unverifiable',0):5.1f}%)",
        "",
        "【数值级别分类（每条数值单独统计）】",
        f"{'类别':<18} {'RAG v3':>18} {'no-RAG':>18}",
        "-" * 58,
        f"{'SUPPORTED ↑':<18}"
        f"  {r.get('num_supported',0):>4} ({r.get('num_pct_supported',0):5.1f}%)"
        f"  {n.get('num_supported',0):>4} ({n.get('num_pct_supported',0):5.1f}%)",
        f"{'CONTRADICTED ↓':<18}"
        f"  {r.get('num_contradicted',0):>4} ({r.get('num_pct_contradicted',0):5.1f}%)"
        f"  {n.get('num_contradicted',0):>4} ({n.get('num_pct_contradicted',0):5.1f}%)",
        "",
        "说明：",
        "  RAG: 对 cited evidence 做核查（直接使用 evidence_ids）",
        "  no-RAG: 对 BM25 post-hoc 检索结果做核查",
        "  CONFLICT = KB 明确针对同一参数给出不同数值（幻觉证据）",
        "=" * 68,
    ]
    return lines


if __name__ == "__main__":
    main()
