# scripts/112_qualitative_experiment_numbers.py
"""汇总五组定性判据补充实验，并生成论文用的宏与表格；另做主实验 RAG 臂的 TBD 成因诊断。

只读：五组生成原始响应、Qwen 评审标签、配对差异和作者 30 条抽查（由 revision_artifacts 下的
运行目录提供），以及主实验结果和 KB。不调用模型。
所有生成行都用论文的统一分级器（grade-v5）重评，使补充实验和主实验口径一致。

输出 data/search_results/exp_v4/qualitative_5arm/qual_numbers.json；
--paper-dir 时写 qualitative_numbers.tex（宏）与 table_qualitative.tex。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import _TBD_PATTERN, classify_grade, valid_citation_ids

RUN = ROOT / "revision_artifacts/qualitative_5arm_authorized_run_20261019"
TERM = RUN / "authorized_remaining330_20261019/terminal_results"
HUMAN = ROOT / "revision_artifacts/human_review_reconciliation_v6_20261019/results/逐项人机对照.csv"
KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
RAG = ROOT / "data/search_results/exp_v4/rag_v4_results.json"
OUT = ROOT / "data/search_results/exp_v4/qualitative_5arm"
GROUPS = ["semantic_old", "semantic_new", "random_old", "random_new", "norag_original"]
POLICY = "numeric-ranges-v1"
HUMAN_MAP = {"直接支持": "direct", "部分支持": "partial", "相矛盾": "contradicted", "证据不足": "insufficient"}
_UNITS = {"°C": r"(?:°C|℃)", "bar": r"bar\b", "MPa": r"MPa", "kPa": r"kPa", "%": r"%", "m³/h": r"(?:m³/h|m3/h)",
          "m3/h": r"(?:m³/h|m3/h)", "L/min": r"L/min", "s": r"(?:s\b|秒)", "min": r"(?:min\b|分钟)", "mm": r"mm\b",
          "rpm": r"rpm", "kW": r"kW", "m/s": r"m/s", "dGH": r"dGH"}
_NONPHYSICAL = {"无", "无量纲", "-", "N/A", "个", "次", "台", "次/周", "图纸标注", "审查项", "选型参数", "流量", "泄漏率", "浓度百分比"}


def _pct(k, n):
    return None if not n else round(100 * k / n, 1)


def _nfkc(s) -> str:
    return unicodedata.normalize("NFKC", "" if s is None else str(s))


def generation_counts(kb: dict) -> dict:
    rows = defaultdict(list)
    for f in sorted((RUN / "generation").glob("*_response.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("status") != "completed":
            continue
        sid, group = r["slot"].split("-", 1)
        for e in (r.get("parsed") or {}).get("shalls", []):
            rows[group].append((sid, e))
    out = {}
    for g in GROUPS:
        rs = rows[g]
        grade = Counter(classify_grade(e.get("measurable_criterion", ""), e.get("evidence_citations", []), kb,
                                       numeric_policy=POLICY) for _, e in rs)
        tbd = [bool(_TBD_PATTERN.search(_nfkc(e.get("measurable_criterion")))) for _, e in rs]
        q = [_nfkc(e.get("measurable_criterion")).lstrip().startswith("[Q]") for _, e in rs]
        cited = [bool(valid_citation_ids(e.get("evidence_citations", []), kb)) for _, e in rs]
        per_src = defaultdict(list)
        for (sid, _), t in zip(rs, tbd):
            per_src[sid].append(t)
        n = len(rs)
        out[g] = {"n_rows": n, "n_sources": len(per_src), **{f"grade_{k}": grade.get(k, 0) for k in "ABCX"},
                  "grade_X_pct": _pct(grade.get("X", 0), n), "grade_AB_pct": _pct(grade.get("A", 0) + grade.get("B", 0), n),
                  "n_tbd": sum(tbd), "tbd_pct": _pct(sum(tbd), n), "n_q": sum(q), "q_pct": _pct(sum(q), n),
                  "citation_pct": _pct(sum(cited), n),
                  "tbd_source_mean_pct": round(100 * sum(sum(v) / len(v) for v in per_src.values()) / len(per_src), 1)}
    return out


def qwen_labels() -> dict:
    groups = json.loads((TERM / "ALL_GROUPS_LABELS_AND_QUALITY.json").read_text(encoding="utf-8"))["groups"]
    out = {}
    for g in ("semantic_new", "random_new"):
        d = groups[g]
        lab = d["machine_label_counts"]
        n = d["valid_response_count"]
        out[g] = {"n_q": d["Q_candidates"], "n_reviewed": n, "support": lab["support"],
                  "applicability": lab["applicability"], "faithfulness": lab["faithfulness"],
                  "verifiability": lab["verifiability"], "anchor": d["anchor_quality_counts"],
                  "direct_pct": _pct(lab["support"].get("direct", 0), n),
                  "partial_pct": _pct(lab["support"].get("partial", 0), n),
                  "insufficient_pct": _pct(lab["support"].get("insufficient", 0), n),
                  "contradicted": lab["support"].get("contradicted", 0),
                  "explicit_match_pct": _pct(lab["applicability"].get("explicit_match", 0), n),
                  "new_inference_pct": _pct(lab["faithfulness"].get("new_inference_or_synthesis", 0)
                                            + lab["faithfulness"].get("unsupported", 0), n),
                  "verifiable_pct": _pct(lab["verifiability"].get("verifiable", 0), n),
                  "anchor_pass_pct": _pct(d["anchor_quality_counts"].get("pass", 0), n)}
    return out


def paired_tests() -> dict:
    d = json.loads((TERM / "PAIRED_SOURCE_REVIEW_DIFFERENCES.json").read_text(encoding="utf-8"))
    rows = [x["raw_label_rate_difference_semantic_minus_random"] for x in d
            if x["semantic_Q"] and x["random_Q"]
            and x["raw_label_rate_difference_semantic_minus_random"]["direct"] is not None]
    ins = [r["insufficient"] for r in rows]
    sup = [r["direct"] + r["partial"] for r in rows]
    return {"n_pairs": len(rows),
            "insufficient_sem_lower": sum(v < 0 for v in ins), "insufficient_sem_higher": sum(v > 0 for v in ins),
            "insufficient_p": float(wilcoxon(ins).pvalue),
            "supported_sem_higher": sum(v > 0 for v in sup), "supported_sem_lower": sum(v < 0 for v in sup),
            "supported_p": float(wilcoxon(sup).pvalue)}


def human_audit() -> dict:
    by = defaultdict(Counter)
    agree = 0
    n = 0
    for r in csv.DictReader(HUMAN.open(encoding="utf-8-sig")):
        if r["计入30条"] != "True":
            continue
        n += 1
        by[r["组别"]][HUMAN_MAP[r["人工支持原值"]]] += 1
        agree += r["支持是否一致"] == "True"
    tot = Counter()
    for c in by.values():
        tot.update(c)
    return {"n": n, "support_agreement": agree, "total": dict(tot), "by_group": {k: dict(v) for k, v in by.items()}}


def deferral_diagnostic(kb: dict) -> dict:
    """主实验 RAG 臂中带有效引用的 TBD：值是否在被引条目原文/抽取列表里。只看物理单位可解析的部分。"""
    d = json.loads(RAG.read_text(encoding="utf-8"))
    c = Counter()
    for rs in d["result_sets"]:
        ev = rs.get("_evidence_values") or {}
        for e in rs["engineering_requirements"]:
            mc = _nfkc(e.get("measurable_criterion"))
            ids = valid_citation_ids(e.get("evidence_citations", []), kb)
            if not _TBD_PATTERN.search(mc) or not ids:
                continue
            m = re.search(r"\{\{?\s*TBD\s*\|\s*(?:unit:)?\s*([^|}]*)", mc)
            unit = (m.group(1).strip() if m else "").replace("℃", "°C")
            if unit in _NONPHYSICAL:
                c["nonnumeric"] += 1
                continue
            key = next((k for k in _UNITS if unit == k or unit.lower().startswith(k.lower())), None)
            if key is None:
                c["other_unit"] += 1
                continue
            pat = re.compile(r"\d+(?:[.,]\d+)?\s*" + _UNITS[key])
            if any(pat.search(_nfkc(f"{v.get('value_text', '')} {v.get('unit', '')}")) for i in ids for v in ev.get(i, [])):
                c["extracted_but_deferred"] += 1
            elif any(pat.search(_nfkc(kb[i].get("text", ""))) for i in ids):
                c["in_text_not_extracted"] += 1
            else:
                c["absent_from_cited_units"] += 1
    c["total"] = sum(c.values())
    return dict(c)


def _p(p: float) -> str:
    return r"$<10^{-5}$" if p < 1e-5 else f"{p:.3f}"


def macros(Q: dict) -> dict:
    g, q, t, h, dd = Q["generation"], Q["qwen"], Q["paired"], Q["human"], Q["deferral"]
    m = {}
    for key, pre in (("semantic_old", "SemOld"), ("semantic_new", "SemNew"), ("random_old", "RndOld"),
                     ("random_new", "RndNew"), ("norag_original", "NoRagRe")):
        a = g[key]
        m.update({pre + "Rows": a["n_rows"], pre + "TbdPct": a["tbd_pct"], pre + "QPct": a["q_pct"], pre + "Q": a["n_q"],
                  pre + "GradeXPct": a["grade_X_pct"], pre + "GradeABPct": a["grade_AB_pct"], pre + "GradeX": a["grade_X"]})
    for key, pre in (("semantic_new", "QSem"), ("random_new", "QRnd")):
        a = q[key]
        m.update({pre + "N": a["n_reviewed"], pre + "DirectPct": a["direct_pct"], pre + "PartialPct": a["partial_pct"],
                  pre + "InsuffPct": a["insufficient_pct"], pre + "Contradicted": a["contradicted"],
                  pre + "MatchPct": a["explicit_match_pct"], pre + "NewInfPct": a["new_inference_pct"],
                  pre + "VerifPct": a["verifiable_pct"], pre + "AnchorPct": a["anchor_pass_pct"]})
    m.update({"QPairs": t["n_pairs"], "QInsLower": t["insufficient_sem_lower"], "QInsHigher": t["insufficient_sem_higher"],
              "QInsP": _p(t["insufficient_p"]), "QSupHigher": t["supported_sem_higher"],
              "QSupLower": t["supported_sem_lower"], "QSupP": _p(t["supported_p"])})
    ht = h["total"]
    m.update({"HumN": h["n"], "HumAgree": h["support_agreement"], "HumDirect": ht.get("direct", 0),
              "HumPartial": ht.get("partial", 0), "HumContra": ht.get("contradicted", 0),
              "HumInsuff": ht.get("insufficient", 0),
              "HumSemInsuff": h["by_group"].get("semantic_new", {}).get("insufficient", 0),
              "HumRndInsuff": h["by_group"].get("random_new", {}).get("insufficient", 0),
              "HumPerArm": h["n"] // 2})
    m.update({"DefTotal": dd["total"], "DefNonNumeric": dd.get("nonnumeric", 0),
              "DefAbsent": dd.get("absent_from_cited_units", 0), "DefExtracted": dd.get("extracted_but_deferred", 0),
              "DefNotExtracted": dd.get("in_text_not_extracted", 0), "DefOtherUnit": dd.get("other_unit", 0)})
    return m


def to_tex(m: dict) -> str:
    lines = ["% generated by scripts/112_qualitative_experiment_numbers.py -- do not edit by hand"]
    for k, v in m.items():
        val = "n/a" if v is None else (f"{v:.1f}\\%" if k.endswith("Pct") else str(v))
        lines.append(f"\\newcommand{{\\{k}}}{{{val}}}")
    return "\n".join(lines) + "\n"


TABLE = r"""\begin{table*}[htbp]
\caption{Five-arm prompt experiment (one window, \texttt{deepseek-flash}, $T=0$; Stage~4 regenerated
on the frozen evidence of the main run). \emph{Old}: numeric value or TBD only; \emph{new}: adds a
cited qualitative criterion marked \texttt{[Q]}. Upper block: all generated rows, graded with the
classifier of Table~\ref{tab:grade}. Lower block: second-LLM (\texttt{qwen-max}) review of every
\texttt{[Q]} criterion against the evidence it cites.\label{tab:qualitative}}
\begin{tabularx}{\textwidth}{X c c c c c}
\toprule
 & \multicolumn{2}{c}{\textbf{Semantic retrieval}} & \multicolumn{2}{c}{\textbf{Random retrieval}} & \textbf{no-RAG} \\
\textbf{Metric} & old & new & old & new & rerun \\
\midrule
Generated shalls & \SemOldRows & \SemNewRows & \RndOldRows & \RndNewRows & \NoRagReRows \\
TBD deferral & \SemOldTbdPct & \SemNewTbdPct & \RndOldTbdPct & \RndNewTbdPct & \NoRagReTbdPct \\
Cited qualitative criterion \texttt{[Q]} & -- & \SemNewQPct & -- & \RndNewQPct & -- \\
Grade A+B (cited numeric value) & \SemOldGradeABPct & \SemNewGradeABPct & \RndOldGradeABPct & \RndNewGradeABPct & \NoRagReGradeABPct \\
Grade X (uncited numeric value) & \SemOldGradeXPct & \SemNewGradeXPct & \RndOldGradeXPct & \RndNewGradeXPct & \NoRagReGradeXPct \\
\midrule
\multicolumn{6}{l}{\emph{Second-LLM review of \texttt{[Q]} criteria} (semantic $n{=}\QSemN$ of \SemNewQ{}, one review returned no valid response; random $n{=}\QRndN$)} \\
Directly supported by cited text & & \QSemDirectPct & & \QRndDirectPct & \\
Partially supported & & \QSemPartialPct & & \QRndPartialPct & \\
Insufficient support & & \QSemInsuffPct & & \QRndInsuffPct & \\
Contradicted & & \QSemContradicted & & \QRndContradicted & \\
Applicability explicitly matched & & \QSemMatchPct & & \QRndMatchPct & \\
New inference or unsupported wording & & \QSemNewInfPct & & \QRndNewInfPct & \\
Judged verifiable & & \QSemVerifPct & & \QRndVerifPct & \\
\bottomrule
\end{tabularx}
\par\smallskip
\begin{minipage}{\textwidth}\footnotesize
Source-level paired comparison over the \QPairs{} requirements with reviewed \texttt{[Q]} criteria in both
retrieval arms: the insufficient-support share is lower under semantic retrieval for \QInsLower{} and
higher for \QInsHigher{} requirements (Wilcoxon $p$\,\QInsP); the supported (direct + partial) share is
higher for \QSupHigher{} and lower for \QSupLower{} (\QSupP). Labels are machine judgements, not
engineering ground truth; see Section~\ref{sec:qualitative} for the author audit.
\end{minipage}
\end{table*}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-dir", type=Path)
    a = ap.parse_args()
    kb = {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}
    Q = {"generation": generation_counts(kb), "qwen": qwen_labels(), "paired": paired_tests(),
         "human": human_audit(), "deferral": deferral_diagnostic(kb), "grading_policy": POLICY}
    Q["macros"] = macros(Q)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "qual_numbers.json").write_text(json.dumps(Q, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.paper_dir:
        (a.paper_dir / "qualitative_numbers.tex").write_text(to_tex(Q["macros"]), encoding="utf-8")
        (a.paper_dir / "table_qualitative.tex").write_text(TABLE, encoding="utf-8")
    print(json.dumps({k: v for k, v in Q.items() if k != "macros"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
