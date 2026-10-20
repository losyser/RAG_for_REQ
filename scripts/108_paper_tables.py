# scripts/108_paper_tables.py
"""Generate the paper macros and the LaTeX tables from the result registry.

Called from scripts/100_paper_numbers.py:  build_macros(N) is merged into the macro
dictionary written to revision_numbers.tex, and write_tables(N) regenerates every
table_*.tex / appendix_sensitivity.tex next to the manuscript.

Missing inputs are rendered as ``n/a`` (macros) or ``n/a`` cells (tables) instead of
raising, so the manuscript still compiles while expert / sensitivity data are pending.
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "data/search_results/exp_v4"
E3 = ROOT / "data/search_results/exp_v3"
PAPER = ROOT.parent / "paper_wiley_submission_to_be_revised"

PCT = r"\%"
ARM_PREFIX = [("Rag", "rag"), ("NoRag", "norag"), ("Random", "random"),
              ("QwenRag", "rag_qwen"), ("QwenNoRag", "norag_qwen")]


# ── helpers ───────────────────────────────────────────────────────────────────
def _load(p):
    p = Path(p)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except Exception:
        return None


def _g(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _n(x, nd=2):
    return None if x is None else round(float(x), nd)


def _pc(x, nd=1):
    return None if x is None else f"{float(x):.{nd}f}" + PCT


def _cell(a, pk, ck=None):
    if not a or a.get(pk) is None:
        return "n/a"
    s = f"{float(a[pk]):.1f}" + PCT
    if ck and a.get(ck) is not None:
        s += f" ({a[ck]})"
    return s


def _ci(a, i):
    ci = (a or {}).get("grade_X_ci")
    if not ci or ci[i] is None:
        return None
    return f"{float(ci[i]):.1f}" + PCT


# ── macros ────────────────────────────────────────────────────────────────────
def build_macros(N: dict) -> dict:
    """Return the macro name -> value map contributed by the result registry.

    Values are scalars (or None for ``n/a``); every name contains letters only so it
    is safe as a LaTeX control sequence.
    """
    N = N or {}
    m: dict = {}

    for prefix, key in ARM_PREFIX:
        a = N.get(key) or {}
        for suffix, field in [("NShalls", "n_shalls"), ("GradeAPct", "grade_A_pct"),
                              ("GradeBPct", "grade_B_pct"), ("GradeCPct", "grade_C_pct"),
                              ("GradeXPct", "grade_X_pct"), ("GradeABPct", "grade_AB_pct"),
                              ("CitationPct", "citation_rate_pct"),
                              ("LoneCitationPct", "l1_citation_rate_pct"),
                              ("MultiSourcePct", "multi_source_pct")]:
            m[prefix + suffix] = a.get(field)
        m[prefix + "GradeXCiLow"] = _ci(a, 0)
        m[prefix + "GradeXCiHigh"] = _ci(a, 1)

    tim = N.get("timing_s_mean") or {}
    for name, field in [("TStageOne", "stage1_s"), ("TRetrieval", "retrieval_s"),
                        ("TSelection", "selection_s"), ("TExtraction", "extraction_s"),
                        ("TGeneration", "generation_s")]:
        m[name] = tim.get(field)
    parts = [tim.get(k) for k in ("stage1_s", "retrieval_s", "selection_s", "extraction_s", "generation_s")]
    m["TTotal"] = _n(sum(parts)) if all(p is not None for p in parts) else None
    m["TTotalMin"] = m["TTotal"]

    leak = N.get("e5_leakage") or {}
    m["LeakMaxCos"] = leak.get("or_max_cos_max")
    m["LeakMedCos"] = leak.get("or_max_cos_median")
    m["LeakKBNNCos"] = leak.get("kb_nn_cos_median")
    m["LeakLCSMax"] = leak.get("or_lcs_chars_max")
    m["LeakNumOR"] = leak.get("n_or_with_numbers")

    s1 = N.get("stage1_sets") or {}
    m["StageOnePairsMean"] = s1.get("pairs_mean")
    m["StageOnePairsMin"] = s1.get("pairs_min")
    m["StageOnePairsMax"] = s1.get("pairs_max")
    m["StageOneFallback"] = s1.get("pairs_fallback")
    m["SelRetrievedMean"] = s1.get("retrieved_mean")
    m["SelSelectedMean"] = N.get("selected_mean")

    m["EncCPUms"] = _g(N.get("encode_latency") or {}, "cpu_ms_per_query")
    m["StageOnePool"] = N.get("e1_pool_n")

    r = N.get("routing") or {}
    rag_routes = _g(r, "rag", "routes") or {}
    reasons = _g(r, "rag", "route_reasons") or {}
    m["RouteOpen"] = rag_routes.get("OPEN_ITEM")
    m["RouteSpot"] = rag_routes.get("SPOT_CHECK")
    m["RouteConfirm"] = rag_routes.get("ENGINEER_CONFIRM")
    m["RouteConfirmTierB"] = next((v for k, v in reasons.items()
                                   if k.startswith("ENGINEER_CONFIRM") and "tier-b" in k), None)
    m["RouteVerify"] = _g(r, "norag", "routes", "VERIFY_OR_REJECT")
    m["RouteAdj"] = r.get("n_conflicts")

    hh = N.get("hhard") or {}
    wx = _g(N.get("credibility") or {}, "h_hard", "wilcoxon") or {}
    m["HhP"] = _n(wx.get("p_value"), 3)
    m["HhRagMean"] = _n(wx.get("rag_mean"), 4)
    m["HhNoRagMean"] = _n(wx.get("norag_mean"), 4)
    m["HhRagPct"] = wx.get("rag_mean") * 100 if wx.get("rag_mean") is not None else None
    m["HhNoRagPct"] = wx.get("norag_mean") * 100 if wx.get("norag_mean") is not None else None
    m["HhPairs"] = wx.get("n_pairs")
    m["HhRagClaims"] = hh.get("rag_claims_checkable")
    m["HhNoRagClaims"] = hh.get("norag_claims_checkable")
    m["HhRagContradictions"] = hh.get("rag_contradictions")
    m["HhNoRagContradictions"] = hh.get("norag_contradictions")
    m["HhRagVerbatim"] = hh.get("rag_numeric_verbatim_from_cited_unit")
    m["HhRagQualitative"] = hh.get("rag_qualitative_contradictions")

    pc = N.get("posthoc") or {}
    m["PosthocRagSupportedPct"] = _g(pc, "rag_v3", "pct_supported")
    m["PosthocRagConflictPct"] = _n(_g(pc, "rag_v3", "pct_conflict"), 1)
    m["PosthocNoRagSupportedPct"] = _g(pc, "no_rag", "pct_supported")
    m["PosthocNoRagConflictPct"] = _n(_g(pc, "no_rag", "pct_conflict"), 1)
    m["PosthocNoRagUnverifiablePct"] = _g(pc, "no_rag", "pct_unverifiable")
    m["RagNumericShalls"] = _g(pc, "rag_v3", "total_shalls")
    m["NoRagNumericShalls"] = _g(pc, "no_rag", "total_shalls")

    cf = N.get("paired_conflict") or {}
    m["ConflictN"] = cf.get("n_paired")
    m["ConflictP"] = _n(cf.get("p_value"), 2)
    m["ConflictRagRatePct"] = _n((cf.get("rag_mean_conflict_rate") or 0) * 100, 2) if cf.get("rag_mean_conflict_rate") is not None else None
    m["ConflictNoRagRatePct"] = _n((cf.get("norag_mean_conflict_rate") or 0) * 100, 2) if cf.get("norag_mean_conflict_rate") is not None else None

    gc = N.get("grade_c") or {}
    br = gc.get("breakdown") or {}
    m["GradeCTotal"] = gc.get("total_grade_c")
    m["GradeCTotalShalls"] = gc.get("total_shalls")
    m["GradeCBreakTBDWithEvidence"] = _g(br, "TBD_with_evidence", "count")
    m["GradeCBreakTBDWithEvidencePct"] = _g(br, "TBD_with_evidence", "pct_of_c")
    m["GradeCBreakTBDNoEvidence"] = _g(br, "TBD_no_evidence", "count")
    m["GradeCBreakQualitative"] = _g(br, "qualitative", "count")
    m["GradeCBreakQualitativePct"] = _g(br, "qualitative", "pct_of_c")

    rp = _g(N.get("regrade_preaudit") or {}, "rag_v4_results.json", "new_with_v3kb") or {}
    ro = _g(N.get("regrade_preaudit") or {}, "rag_v4_results.json", "old") or {}
    m["PreAuditRagA"] = rp.get("A")
    m["PreAuditRagB"] = rp.get("B")
    m["PreAuditRagC"] = rp.get("C")
    m["PreAuditRagX"] = rp.get("X")
    m["PreAuditRagXOld"] = ro.get("X") if ro else None
    m["PreAuditRagBOld"] = ro.get("B") if ro else None
    m["PreAuditRagAOld"] = ro.get("A") if ro else None
    m["PreAuditRagCOld"] = ro.get("C") if ro else None

    bd = N.get("e3_boundary") or {}
    m["SensUsedUnits"] = bd.get("n_used_units")
    m["BoundaryEUSplit"] = _g(bd, "eu_atomic", "split_pct")
    by_window = {w.get("window"): w.get("split_pct")
                 for w in (bd.get("fixed_windows") or []) if not w.get("overlap")}
    for window, name in ((128, "BoundaryWSmall"), (256, "BoundaryWMid"), (512, "BoundaryWLarge")):
        m[name] = by_window.get(window)
    by_window_ov = {w.get("window"): w.get("split_pct")
                    for w in (bd.get("fixed_windows") or []) if w.get("overlap")}
    m["BoundaryWSmallOvPct"] = by_window_ov.get(128)
    m["BoundaryUnitsOverPrompt"] = bd.get("pct_used_units_longer_than_prompt_limit")
    m["BoundaryValuesBeyondPrompt"] = bd.get("pct_values_beyond_prompt_limit")

    sens = N.get("e3_sensitivity") or {}
    ret = sens.get("retrieval") or {}
    wj = [d.get("jaccard_vs_default_mean") for k, d in ret.items() if k.startswith("w_bm25")]
    wj = [v for v in wj if v is not None]
    m["SensJWeightLow"] = min(wj) if wj else None
    m["SensJWeightHigh"] = max(wj) if wj else None
    k0 = [d.get("jaccard_vs_default_mean") for k, d in ret.items() if k.startswith("k0")]
    k0 = [v for v in k0 if v is not None]
    m["SensJKzero"] = k0[0] if k0 and all(v == k0[0] for v in k0) else None
    m["SensJKfour"] = _g(ret, "k_4", "jaccard_vs_default_mean")
    m["SensJMpnet"] = _g(ret, "embed_mpnet", "jaccard_vs_default_mean")
    e2e = sens.get("e2e") or {}
    ab = [d.get("grade_AB_pct") for d in e2e.values() if d.get("grade_AB_pct") is not None]
    gx = [d.get("grade_X_pct") for d in e2e.values() if d.get("grade_X_pct") is not None]
    m["SensABLowPct"] = min(ab) if ab else None
    m["SensABHighPct"] = max(ab) if ab else None
    m["SensGradeXMaxPct"] = max(gx) if gx else None

    ex = N.get("expert") or {}
    m["ExpertNtag"] = ex.get("n_tagged")
    m["KappaComp"] = ex.get("kappa_component")
    m["KappaIntent"] = ex.get("kappa_intent")
    m["KappaPair"] = ex.get("kappa_pair")

    ev = _g(N.get("credibility") or {}, "blind_quality", "aggregate") or {}
    for dim in ("completeness", "actionability", "consistency", "verifiability", "overall"):
        d = ev.get(dim) or {}
        m["Blind" + dim.capitalize() + "R"] = d.get("R")
        m["Blind" + dim.capitalize() + "B"] = d.get("B0")
        m["Blind" + dim.capitalize() + "Tie"] = d.get("tie")
    ov = ev.get("overall") or {}
    parts = [ov.get("R"), ov.get("B0"), ov.get("tie")]
    m["BlindOverallN"] = sum(parts) if all(p is not None for p in parts) else None
    return m


# ── table builders ────────────────────────────────────────────────────────────
def table_descriptive(N: dict) -> str:
    N = N or {}
    rag, norag = N.get("rag") or {}, N.get("norag") or {}
    desc = _g(N.get("credibility") or {}, "descriptive") or {}
    num_r = _n((_g(desc, "rag_v3", "numeric_fraction") or 0) * 100, 1) if _g(desc, "rag_v3", "numeric_fraction") is not None else None
    num_n = _n((_g(desc, "no_rag", "numeric_fraction") or 0) * 100, 1) if _g(desc, "no_rag", "numeric_fraction") is not None else None
    na = "n/a"
    n_src = rag.get("n_sets", na)
    return (
        "\\begin{table*}[htbp]\n"
        f"\\caption{{Descriptive statistics for the RAG and no-RAG arms across {n_src} source requirements."
        "\\label{tab:descriptive}}\n"
        "\\begin{tabularx}{\\textwidth}{X >{\\centering\\arraybackslash}p{3.2cm} >{\\centering\\arraybackslash}p{3.2cm}}\n"
        "\\toprule\n"
        "\\textbf{Metric} & \\textbf{RAG} & \\textbf{no-RAG} \\\\\n"
        "\\midrule\n"
        f"Total source requirements & {n_src} & {norag.get('n_sets', na)} \\\\\n"
        f"Total engineering requirements & {rag.get('n_shalls', na)} & {norag.get('n_shalls', na)} \\\\\n"
        f"Shall statements containing a number & {num_r if num_r is not None else na}\\% & {num_n if num_n is not None else na}\\% \\\\\n"
        f"Per-shall KB attribution & {_pc(rag.get('citation_rate_pct')) or na} & {_pc(norag.get('citation_rate_pct')) or na} \\\\\n"
        "\\bottomrule\n"
        "\\end{tabularx}\n\\end{table*}\n"
    )


def table_grade(N: dict) -> str:
    N = N or {}
    rag, norag = N.get("rag") or {}, N.get("norag") or {}
    na = "n/a"
    return (
        "\\begin{table*}[htbp]\n"
        "\\caption{Numeric provenance-grade distribution of generated ``shall'' statements"
        f" (RAG $n{{=}}\\RagNShalls$; no-RAG $n{{=}}\\NoRagNShalls$).  Each shall is graded by numeric-pattern"
        " and citation-metadata checks on its \\texttt{measurable\\_criterion}:"
        " \\textbf{A}~--~precise value with an L1 (regulatory) citation and a clause reference;"
        " \\textbf{B}~--~value with a valid KB citation;"
        " \\textbf{C}~--~TBD placeholder or no recognized numeric-unit pattern;"
        " \\textbf{X}~--~a concrete numeric value with \\emph{no} verifiable citation."
        "  Grades describe traceability, not semantic support.\\label{tab:grade}}\n"
        "\\begin{tabularx}{\\textwidth}{X >{\\centering\\arraybackslash}p{2.6cm} >{\\centering\\arraybackslash}p{2.6cm}}\n"
        "\\toprule\n"
        "\\textbf{Grade} & \\textbf{RAG} & \\textbf{no-RAG} \\\\\n"
        "\\midrule\n"
        f"A~(precise value $+$ L1 clause) $\\uparrow$ & {_cell(rag,'grade_A_pct','grade_A')} & {_cell(norag,'grade_A_pct','grade_A')} \\\\\n"
        f"B~(value $+$ any citation) $\\uparrow$ & {_cell(rag,'grade_B_pct','grade_B')} & {_cell(norag,'grade_B_pct','grade_B')} \\\\\n"
        f"C~(TBD or no recognized numeric pattern) & {_cell(rag,'grade_C_pct','grade_C')} & {_cell(norag,'grade_C_pct','grade_C')} \\\\\n"
        f"\\textbf{{X~(untraceable value)}} $\\downarrow$ & \\textbf{{{_cell(rag,'grade_X_pct','grade_X')}}} & \\textbf{{{_cell(norag,'grade_X_pct','grade_X')}}} \\\\\n"
        "\\midrule\n"
        f"KB citation rate $\\uparrow$ & {_pc(rag.get('citation_rate_pct')) or na} & {_pc(norag.get('citation_rate_pct')) or na} \\\\\n"
        f"L1 (regulatory) citation rate $\\uparrow$ & {_pc(rag.get('l1_citation_rate_pct')) or na} & {_pc(norag.get('l1_citation_rate_pct')) or na} \\\\\n"
        "\\bottomrule\n\\end{tabularx}\n\\end{table*}\n"
    )


def _arm_rows(a: dict) -> list:
    return [("Total shalls", str(a.get("n_shalls", "n/a"))),
            ("Grade A", _cell(a, "grade_A_pct", "grade_A")),
            ("Grade B", _cell(a, "grade_B_pct", "grade_B")),
            ("Grade C", _cell(a, "grade_C_pct", "grade_C")),
            ("Grade X", _cell(a, "grade_X_pct", "grade_X")),
            ("Grade A+B", _pc(a.get("grade_AB_pct")) or "n/a"),
            ("KB citation rate", _pc(a.get("citation_rate_pct")) or "n/a"),
            ("L1 citation rate", _pc(a.get("l1_citation_rate_pct")) or "n/a")]


def table_ablation(N: dict) -> str:
    N = N or {}
    arms = [("RAG", N.get("rag") or {}), ("Random retrieval", N.get("random") or {}),
            ("no-RAG", N.get("norag") or {})]
    rows = [_arm_rows(a) for _, a in arms]
    body = "\n".join(
        f"{label} & " + " & ".join(r[i][1] for r in rows) + r" \\" for i, (label, _) in enumerate(rows[0])
    )
    return (
        "\\begin{table*}[htbp]\n"
        "\\caption{Retrieval ablation: semantic (hybrid) retrieval vs.\\ random retrieval vs.\\ no retrieval. "
        "Grade definitions as in Table~\\ref{tab:grade}.\\label{tab:ablation}}\n"
        "\\begin{tabularx}{\\textwidth}{X >{\\centering\\arraybackslash}p{2.4cm} >{\\centering\\arraybackslash}p{2.4cm} >{\\centering\\arraybackslash}p{2.4cm}}\n"
        "\\toprule\n"
        "\\textbf{Metric} & \\textbf{RAG} & \\textbf{Random} & \\textbf{no-RAG} \\\\\n"
        "\\midrule\n" + body + "\n\\bottomrule\n\\end{tabularx}\n\\end{table*}\n"
    )


def table_posthoc(N: dict) -> str:
    pc = N.get("posthoc") or {}
    rag, norag = pc.get("rag_v3") or {}, pc.get("no_rag") or {}
    na = "n/a"

    def row(label, d, key):
        v = d.get(key)
        return f"{label} & {_pc(v) if v is not None else na} \\\\"
    return (
        "\\begin{table}[htbp]\n"
        "\\caption{Post-hoc verification of numeric shall statements against the audited KB."
        "\\label{tab:posthoc}}\n"
        "\\begin{tabularx}{\\textwidth}{X >{\\centering\\arraybackslash}p{3.0cm} >{\\centering\\arraybackslash}p{3.0cm}}\n"
        "\\toprule\n"
        "\\textbf{Outcome} & \\textbf{RAG} & \\textbf{no-RAG} \\\\\n"
        "\\midrule\n"
        f"Numeric shalls checked & {rag.get('total_shalls', na)} & {norag.get('total_shalls', na)} \\\\\n"
        f"Supported by KB & {_pc(rag.get('pct_supported')) or na} & {_pc(norag.get('pct_supported')) or na} \\\\\n"
        f"Contradicted by KB & {_pc(rag.get('pct_conflict')) or na} & {_pc(norag.get('pct_conflict')) or na} \\\\\n"
        f"Unverifiable & {_pc(rag.get('pct_unverifiable')) or na} & {_pc(norag.get('pct_unverifiable')) or na} \\\\\n"
        "\\bottomrule\n\\end{tabularx}\n\\end{table}\n"
    )


def table_crossllm(N: dict) -> str:
    N = N or {}
    na = "n/a"
    rows = [("RAG \\texttt{deepseek}", N.get("rag") or {}), ("RAG \\texttt{qwen-max}", N.get("rag_qwen") or {}),
            ("no-RAG \\texttt{deepseek}", N.get("norag") or {}), ("no-RAG \\texttt{qwen-max}", N.get("norag_qwen") or {})]
    body = "\n".join(
        f"{label} & {a.get('n_shalls', na)} & {_pc(a.get('grade_X_pct')) or na} & {_pc(a.get('grade_AB_pct')) or na} & {_pc(a.get('citation_rate_pct')) or na} \\\\"
        for label, a in rows)
    return (
        "\\begin{table}[htbp]\n"
        "\\caption{Cross-generator robustness: the same pipeline under two generator LLMs."
        "\\label{tab:crossllm}}\n"
        "\\begin{tabularx}{\\textwidth}{X r r r r}\n"
        "\\toprule\n"
        "\\textbf{Arm} & \\textbf{Shalls} & \\textbf{Grade X} & \\textbf{Grade A+B} & \\textbf{Citation} \\\\\n"
        "\\midrule\n" + body + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n"
    )


def table_blind_eval(N: dict) -> str:
    agg = _g(N.get("credibility") or {}, "blind_quality", "aggregate") or {}
    na = "n/a"
    lines = []
    for dim in ("completeness", "actionability", "consistency", "verifiability"):
        d = agg.get(dim) or {}
        r, t, b = d.get("R", 0) or 0, d.get("tie", 0) or 0, d.get("B0", 0) or 0
        n = r + t + b
        rate = _pc(100.0 * r / n) if n else na
        lines.append(f"{dim.capitalize()} & {r} & {t} & {b} & {rate} \\\\")
    ov = agg.get("overall") or {}
    r, t, b = ov.get("R", 0) or 0, ov.get("tie", 0) or 0, ov.get("B0", 0) or 0
    n = r + t + b
    lines.append("\\midrule")
    lines.append(f"\\textbf{{Overall}} & {r} & {t} & {b} & {_pc(100.0 * r / n) if n else na} \\\\")
    return (
        "\\begin{table}[htbp]\n"
        "\\caption{Blind pairwise quality evaluation (RAG vs.\\ no-RAG), left--right swap applied to"
        " remove position bias. R = RAG wins, B = no-RAG wins, Tie = no preference."
        "\\label{tab:blind_eval}}\n"
        "\\begin{tabular}{lcccc}\n"
        "\\toprule\n"
        "\\textbf{Dimension} & \\textbf{R (RAG)} & \\textbf{Tie} & \\textbf{B (no-RAG)} & \\textbf{Win rate (R)} \\\\\n"
        "\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_hhard(N: dict) -> str:
    hh = _g(N.get("credibility") or {}, "h_hard") or {}
    wx = hh.get("wilcoxon") or {}
    na = "n/a"

    def stats(src):
        vals = [v.get("h_hard") for v in (hh.get(src) or {}).values() if v.get("h_hard") is not None]
        if not vals:
            return na, na
        return f"{st.mean(vals):.4f}", f"{(st.pstdev(vals)):.4f}"
    rm, rs = stats("rag_v3")
    nm, ns = stats("no_rag")
    p = wx.get("p_value")
    p_str = f"{p:.3f}" if p is not None else na
    n_pairs = wx.get("n_pairs", "n/a")
    return (
        "\\begin{table}[htbp]\n"
        "\\caption{H$_{\\mathrm{hard}}$ contradiction rate of checkable numeric claims per source requirement"
        " (paired Wilcoxon signed-rank test, $n=" + str(n_pairs) + "$).\\label{tab:hhard}}\n"
        "\\begin{tabular}{lcc}\n"
        "\\toprule\n"
        "\\textbf{Arm} & \\textbf{Mean $H_{\\mathrm{hard}}$} & \\textbf{Std} \\\\\n"
        "\\midrule\n"
        f"RAG & {rm} & {rs} \\\\\n"
        f"no-RAG & {nm} & {ns} \\\\\n"
        "\\midrule\n"
        f"\\multicolumn{{3}}{{l}}{{Wilcoxon $p={p_str}$ (RAG higher)}} \\\\\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_routing(N: dict) -> str:
    r = _g(N.get("routing") or {}, "rag") or {}
    der = r.get("derivation") or {}
    routes = r.get("routes") or {}
    total = (N.get("rag") or {}).get("n_shalls")
    na = "n/a"

    def pct(v):
        return _pc(100.0 * v / total) if (v is not None and total) else na
    lines = ["\\multicolumn{3}{l}{\\emph{Derivation type}} \\\\"]
    for k in ("Deferred", "Direct", "Synthesized", "Derived", "Unsupported"):
        if der.get(k) is None:
            continue
        lines.append(f"{k} & {der[k]} & {pct(der[k])} \\\\")
    lines.append("\\midrule")
    lines.append("\\multicolumn{3}{l}{\\emph{Review route}} \\\\")
    for k, label in (("OPEN_ITEM", "Open item"), ("ENGINEER_CONFIRM", "Engineer confirm"),
                     ("ADJUDICATE", "Adjudicate (candidate conflict)"), ("SPOT_CHECK", "Spot-check")):
        if routes.get(k) is None:
            continue
        lines.append(f"{label} & {routes[k]} & {pct(routes[k])} \\\\")
    return (
        "\\begin{table}[htbp]\n"
        "\\caption{Derivation types and review routing for the RAG arm"
        f" ($n{{=}}\\RagNShalls$).\\label{{tab:routing}}}}\n"
        "\\begin{tabularx}{\\linewidth}{X r r}\n"
        "\\toprule\n"
        "\\textbf{Category} & \\textbf{Count} & \\textbf{\\% of shalls} \\\\\n"
        "\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n"
    )


def _na_table(label: str, caption: str, note: str) -> str:
    return (
        "\\begin{table}[htbp]\n"
        f"\\caption{{{caption}\\label{{{label}}}}}\n"
        "\\begin{tabularx}{\\textwidth}{X}\n\\toprule\n"
        f"{note} \\\\\n"
        "\\bottomrule\n\\end{tabularx}\n\\end{table}\n"
    )


def table_e1(N: dict) -> str:
    return _na_table("tab:e1", "Stage~1 (component, aspect) mapping accuracy (E1).",
                     "Pending expert gold labels (workbook S2).")


def table_blind_correct(N: dict) -> str:
    return _na_table("tab:blind_correct", "Blind correctness of numeric values (S3).",
                     "Pending expert blind assessment (workbook S3).")


def table_stage3(N: dict) -> str:
    return _na_table("tab:stage3", "Stage~3 extraction accuracy (S4).",
                     "Pending expert extraction review (workbook S4).")


def table_sensitivity(N: dict) -> str:
    sens = N.get("e3_sensitivity") or {}
    ret = sens.get("retrieval") or {}
    if not ret:
        return _na_table("tab:sensitivity", "Retrieval sensitivity (E3).",
                         "Pending sensitivity runs (script 99).")
    lines = []
    for name, d in ret.items():
        lines.append(f"{name.replace('_', chr(92) + '_')} & {d.get('units_per_req_mean','n/a')} & "
                     f"{_pc(d.get('l1_share_pct')) or 'n/a'} & {_pc(d.get('numeric_unit_share_pct')) or 'n/a'} & "
                     f"{d.get('jaccard_vs_default_mean','n/a')} \\\\")
    return (
        "\\begin{table*}[htbp]\n"
        "\\caption{Retrieval-layer metrics across retrieval variants (E3).\\label{tab:sensitivity}}\n"
        "\\begin{tabularx}{\\textwidth}{X r r r r}\n"
        "\\toprule\n"
        "\\textbf{Variant} & \\textbf{Units/req} & \\textbf{L1 share} & \\textbf{Numeric share} & \\textbf{Jaccard} \\\\\n"
        "\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabularx}\n\\end{table*}\n"
    )


def appendix_sensitivity(N: dict) -> str:
    sens = N.get("e3_sensitivity") or {}
    ret, e2e = sens.get("retrieval") or {}, sens.get("e2e") or {}
    if not ret and not e2e:
        out = ["\\section{Sensitivity Analysis}\n\\label{app:sensitivity}\n"]
        out.append("Pending sensitivity runs (script 99): the retrieval-variant and end-to-end tables "
                   "will be regenerated by \\texttt{scripts/108\\_paper\\_tables.py} once available.\n")
        return "\n".join(out)
    # USG is a two-column class; these wide tables need a full-width page.
    out = ["\\onecolumn\n", "\\section{Sensitivity Analysis}\n\\label{app:sensitivity}\n"]
    if ret:
        out.append("\\begin{table}[htbp]\n\\caption{Retrieval-layer metrics across retrieval variants.}"
                   "\\label{tab:app_retrieval}\n\\begin{tabularx}{\\textwidth}{X r r r r}\n\\toprule\n"
                   "\\textbf{Variant} & \\textbf{Units/req} & \\textbf{L1 share} & \\textbf{Numeric share} & \\textbf{Jaccard} \\\\\n\\midrule\n")
        for name, d in ret.items():
            out.append(f"{name.replace('_', chr(92) + '_')} & {d.get('units_per_req_mean','n/a')} & "
                       f"{_pc(d.get('l1_share_pct')) or 'n/a'} & {_pc(d.get('numeric_unit_share_pct')) or 'n/a'} & "
                       f"{d.get('jaccard_vs_default_mean','n/a')} \\\\")
        out.append("\\bottomrule\n\\end{tabularx}\n\\end{table}\n")
    if e2e:
        out.append("\\begin{table}[htbp]\n\\caption{End-to-end grade distribution across retrieval variants.}"
                   "\\label{tab:app_e2e}\n\\begin{tabularx}{\\textwidth}{X r r r r}\n\\toprule\n"
                   "\\textbf{Variant} & \\textbf{Shalls} & \\textbf{Grade X} & \\textbf{Grade A+B} & \\textbf{Citation} \\\\\n\\midrule\n")
        for name, d in e2e.items():
            out.append(f"{name.replace('_', chr(92) + '_')} & {d.get('n_shalls','n/a')} & "
                       f"{_pc(d.get('grade_X_pct')) or 'n/a'} & {_pc(d.get('grade_AB_pct')) or 'n/a'} & "
                       f"{_pc(d.get('citation_rate_pct')) or 'n/a'} \\\\")
        out.append("\\bottomrule\n\\end{tabularx}\n\\end{table}\n")
    out.append("\\twocolumn\n")
    return "\n".join(out)


TABLES = {
    "table_descriptive.tex": table_descriptive,
    "table_grade.tex": table_grade,
    "table_ablation.tex": table_ablation,
    "table_posthoc.tex": table_posthoc,
    "table_crossllm.tex": table_crossllm,
    "table_blind_eval.tex": table_blind_eval,
    "table_hhard.tex": table_hhard,
    "table_routing.tex": table_routing,
    "table_e1.tex": table_e1,
    "table_blind_correct.tex": table_blind_correct,
    "table_stage3.tex": table_stage3,
    "table_sensitivity.tex": table_sensitivity,
    "appendix_sensitivity.tex": appendix_sensitivity,
}


def write_tables(N: dict, dest: Path = PAPER) -> list:
    dest = Path(dest)
    written = []
    for fname, fn in TABLES.items():
        p = dest / fname
        p.write_text(fn(N), encoding="utf-8")
        written.append(p.name)
    return written


def main() -> None:
    N = _load(E4 / "paper_numbers.json") or {}
    for name in write_tables(N):
        print("wrote", name)


if __name__ == "__main__":
    main()
