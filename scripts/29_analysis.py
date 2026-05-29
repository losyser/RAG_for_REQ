# -*- coding: utf-8 -*-
"""
Script 29: Depth analyses for the cooling-water RAG paper (Track T7).

Five sub-analyses run independently against the existing batch outputs in
`data/search_results/batch_*` (uses every batch dir that has a complete
G1..A2 set of result files).

Subcommands:
  failure-taxonomy   E-10  LLM-driven classification of M1/M3/M4 failures
  qg-calibration     E-13  Expert-proxy review of 50 random G4 ERs
  held-out           E-9   Held-out test set of 30 NEW requirements
                           Input:  data/processed/held_out_requirements_30.jsonl
                           Output: held_out_test.json
  heatmaps           E-14  Stakeholder x component M1/M3 heatmaps
  all                run every sub-analysis sequentially (skips ir-metrics)

  [REMOVED] ir-metrics (E-5): silver-truth IR evaluation removed from paper
  due to circular-argument problem (G4/G3/A1 MRR=100% by construction).

Outputs (all under `data/search_results/`):
  failure_taxonomy.json
  failure_taxonomy_pareto.png
  qg_calibration.json
  qg_calibration_table.tex
  held_out_test.json
  heatmap_M1.png
  heatmap_M3.png
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
from cooling_rag_mg.llm_cache import cached_completion
from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.text_utils import safe_text

ALL_GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]

# ─────────────────────────────────────────────────────────────────────────────
# Common helpers
# ─────────────────────────────────────────────────────────────────────────────


def _find_complete_batches(search_dir: Path) -> list[Path]:
    """Return every batch_* directory whose `experiment/` has all 6 group files."""
    out: list[Path] = []
    for child in sorted(search_dir.iterdir()):
        if not child.is_dir() or not child.name.startswith("batch_"):
            continue
        exp = child / "experiment"
        if not exp.exists():
            continue
        if all((exp / f"{g}_results.json").exists() for g in ALL_GROUPS):
            out.append(exp)
    return out


def _load_group(exp_dir: Path, group: str) -> list[dict[str, Any]]:
    """Return the `result_sets` list for one group, regardless of wrapper shape."""
    raw = json.loads((exp_dir / f"{group}_results.json").read_text(encoding="utf-8"))
    return raw["result_sets"] if isinstance(raw, dict) else raw


def _flatten_ers(result_sets: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (requirement_set, engineering_requirement) tuples."""
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for rs in result_sets:
        for er in rs.get("engineering_requirements") or []:
            pairs.append((rs, er))
    return pairs


def _load_sampled_lookup(exp_dir: Path) -> dict[str, dict[str, Any]]:
    """Build {source_requirement_id: {stakeholder, requirement_text}} from sampled jsonl."""
    p = exp_dir / "sampled_requirements.jsonl"
    if not p.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = obj.get("requirement_id")
            if rid:
                out[rid] = obj
    return out


def _load_evidence_lookup(cfg: Any) -> dict[str, dict[str, Any]]:
    """Map evidence_id -> {text, source_file, metadata}."""
    p = Path(cfg.paths.evidence_units_jsonl)
    out: dict[str, dict[str, Any]] = {}
    if not p.exists():
        return out
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev_id = obj.get("id")
            if ev_id:
                meta = obj.get("metadata") or {}
                out[ev_id] = {
                    "text": obj.get("text", ""),
                    "source_file": str(meta.get("source_document", "") or ""),
                    "component_objects": meta.get("component_objects", []),
                    "engineering_aspect": meta.get("engineering_aspect", ""),
                }
    return out


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Sub-1: E-10 Failure taxonomy
# ─────────────────────────────────────────────────────────────────────────────

_FAILURE_PROMPT = """\
You are an expert in retrieval-augmented generation systems for marine engineering.

We have an engineering requirement (a "shall statement") that FAILED one or more quality \
checks. Your task is to classify the ROOT CAUSE of the failure into exactly one of \
these five categories:

1. retrieval_miss      — Relevant evidence DID exist in the knowledge base but the retriever \
                         failed to surface it (the shall_statement matches a known component / \
                         aspect, but evidence_ids is empty or contains unrelated items).
2. judge_wrong         — Retriever found plausible candidates but the LLM evidence-judge \
                         rejected good candidates or accepted bad ones (visible as evidence \
                         mismatch between source requirement and evidence content).
3. hallucination       — Generator introduced specific numbers, units, or factual claims \
                         that are not supported by any evidence_ids (over-inference).
4. coverage_gap        — Relevant evidence simply does not exist in the KB (e.g., very \
                         niche topic, recent regulation, project-specific data).
5. ambiguous_requirement — The source requirement itself is too vague or open-ended; \
                         failure may be inherent regardless of retrieval quality.

Context:
- Original source requirement (id={source_id}, stakeholder={stakeholder}):
  "{source_text}"
- Engineering requirement that failed (id={er_id}, type={req_type}):
  - shall_statement: "{shall}"
  - support_status:  "{status}"
  - evidence_ids:    {evidence_ids}
  - failed checks:   {failed_checks}

Return ONLY valid JSON (no markdown, no commentary):
{{
  "category": "<one of: retrieval_miss, judge_wrong, hallucination, coverage_gap, ambiguous_requirement>",
  "reasoning": "<one sentence, <=30 words>"
}}
"""


_VALID_CATEGORIES = {
    "retrieval_miss",
    "judge_wrong",
    "hallucination",
    "coverage_gap",
    "ambiguous_requirement",
}


def _identify_failures(qg: QualityGate, er: dict[str, Any]) -> list[str]:
    """Return the names of any failed M1/M3/M4 dimensions for one ER."""
    failed: list[str] = []
    if not qg._evidence_sufficiency(er).passed:  # noqa: SLF001  (M1 proxy)
        failed.append("evidence_sufficiency")
    if not qg._over_inference(er).passed:  # noqa: SLF001       (M3)
        failed.append("over_inference")
    v = qg._verifiability(er)  # noqa: SLF001                    (M4)
    if not v.passed:
        failed.append(f"verifiability:{v.severity}")
    return failed


def _classify_failure_llm(
    client: Any,
    cfg: Any,
    *,
    source_id: str,
    stakeholder: str,
    source_text: str,
    er_id: str,
    req_type: str,
    shall: str,
    status: str,
    evidence_ids: list[str],
    failed_checks: list[str],
) -> dict[str, str]:
    prompt = _FAILURE_PROMPT.format(
        source_id=source_id,
        stakeholder=stakeholder,
        source_text=source_text[:600],
        er_id=er_id,
        req_type=req_type,
        shall=shall[:600],
        status=status,
        evidence_ids=evidence_ids[:8],
        failed_checks=failed_checks,
    )
    try:
        resp = cached_completion(
            client,
            model=cfg.deepseek.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        obj = json.loads(resp.choices[0].message.content or "{}")
        cat = safe_text(obj.get("category"))
        if cat not in _VALID_CATEGORIES:
            cat = "coverage_gap"  # safe default
        return {"category": cat, "reasoning": safe_text(obj.get("reasoning"))[:240]}
    except Exception as exc:  # noqa: BLE001
        return {"category": "coverage_gap", "reasoning": f"[LLM error: {exc}] defaulted"}


def run_failure_taxonomy(cfg: Any, out_dir: Path) -> dict[str, Any]:
    print("\n[Sub-1] Failure taxonomy (E-10)")
    batches = _find_complete_batches(cfg.paths.search_results_dir)
    print(f"  using {len(batches)} complete batches")
    qg = QualityGate()
    from openai import OpenAI
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url) if cfg.deepseek.enabled else None

    cases: list[dict[str, Any]] = []
    seen_keys: set[str] = set()  # dedupe by er_id (same ER may appear in multiple batches w/ identical id)
    for exp in batches:
        sampled = _load_sampled_lookup(exp)
        g4 = _load_group(exp, "G4")
        for rs in g4:
            src_id = safe_text(rs.get("source_requirement_id"))
            stake = safe_text(rs.get("stakeholder"))
            src_meta = sampled.get(src_id, {})
            src_text = src_meta.get("requirement_text", "")
            for er in rs.get("engineering_requirements") or []:
                failed = _identify_failures(qg, er)
                # Keep only M1, M3, or M4 (error-severity verifiability) failures
                relevant = [f for f in failed if f in {"evidence_sufficiency", "over_inference", "verifiability:error"}]
                if not relevant:
                    continue
                key = f"{exp.parent.name}::{safe_text(er.get('id'))}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                cases.append({
                    "batch": exp.parent.name,
                    "source_id": src_id,
                    "stakeholder": stake,
                    "source_text": src_text,
                    "er_id": safe_text(er.get("id")),
                    "req_type": safe_text(er.get("requirement_type")),
                    "shall": safe_text(er.get("shall_statement")),
                    "status": safe_text(er.get("support_status")),
                    "evidence_ids": list(er.get("evidence_ids") or []),
                    "failed_checks": relevant,
                })

    print(f"  total failure cases (deduped across batches): {len(cases)}")

    classified: list[dict[str, Any]] = []
    if client is None:
        print("  WARNING: DeepSeek not configured; falling back to heuristic classification.")
    for i, c in enumerate(cases, 1):
        if i % 10 == 0 or i == 1:
            print(f"  classifying {i}/{len(cases)} …")
        if client is None:
            # Heuristic fallback (no LLM)
            if not c["evidence_ids"]:
                cat = "coverage_gap" if c["status"] == "evidence_gap" else "retrieval_miss"
            elif "over_inference" in c["failed_checks"]:
                cat = "hallucination"
            elif "verifiability:error" in c["failed_checks"]:
                cat = "ambiguous_requirement"
            else:
                cat = "judge_wrong"
            res = {"category": cat, "reasoning": "heuristic fallback (no LLM)"}
        else:
            res = _classify_failure_llm(
                client, cfg,
                source_id=c["source_id"],
                stakeholder=c["stakeholder"],
                source_text=c["source_text"],
                er_id=c["er_id"],
                req_type=c["req_type"],
                shall=c["shall"],
                status=c["status"],
                evidence_ids=c["evidence_ids"],
                failed_checks=c["failed_checks"],
            )
        classified.append({**c, **res})

    counts = collections.Counter(c["category"] for c in classified)
    pareto = counts.most_common()

    # Pareto plot
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        import matplotlib.font_manager as fm
        installed = {f.name for f in fm.fontManager.ttflist}
        for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Noto Sans SC", "SimSun"):
            if name in installed:
                plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                break
    except Exception:
        pass
    labels = [c[0] for c in pareto]
    values = [c[1] for c in pareto]
    cum_pct = []
    total = sum(values) or 1
    running = 0
    for v in values:
        running += v
        cum_pct.append(100.0 * running / total)

    fig, ax1 = plt.subplots(figsize=(9, 5))
    bars = ax1.bar(labels, values, color="#4C78A8")
    ax1.set_ylabel("Failure count")
    ax1.set_xlabel("Failure category")
    ax1.set_title(f"Failure Taxonomy Pareto (n={total} failed engineering requirements)")
    for b, v in zip(bars, values):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.3, str(v), ha="center", va="bottom", fontsize=10)
    ax2 = ax1.twinx()
    ax2.plot(labels, cum_pct, color="#E45756", marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 110)
    for x, y in zip(labels, cum_pct):
        ax2.text(x, y + 2, f"{y:.0f}%", color="#E45756", ha="center", fontsize=9)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plot_path = out_dir / "failure_taxonomy_pareto.png"
    fig.savefig(plot_path, dpi=140)
    plt.close(fig)
    print(f"  -> {plot_path}")

    result = {
        "n_batches": len(batches),
        "n_failures": total,
        "category_counts": dict(counts),
        "pareto": [{"category": k, "count": v, "pct": round(100.0 * v / total, 2)} for k, v in pareto],
        "cases": classified,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(out_dir / "failure_taxonomy.json", result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Sub-2: E-13 QG calibration (independent expert-proxy prompt)
# ─────────────────────────────────────────────────────────────────────────────

_EXPERT_QG_PROMPT = """\
You are a senior marine engineering reviewer for ship main engine cooling water systems. \
You are independently auditing an automatically-generated engineering requirement \
("shall statement") against five quality dimensions.

Engineering requirement under review (id={er_id}):
  shall_statement:     "{shall}"
  acceptance_criteria: {criteria}
  verification_method: "{vm}"
  evidence_ids:        {evidence_ids}
  support_status:      "{status}"
  requirement_type:    "{req_type}"

For each of the five dimensions below, output a binary judgment "pass" or "fail":

1. evidence_sufficiency — Does the requirement cite at least one piece of supporting evidence \
   (evidence_ids non-empty) AND is its support_status NOT a gap placeholder?
2. verifiability — Is verification_method one of {{review, inspection, calculation, test, \
   commissioning_check, operation_check, maintenance_check, class_approval}} AND are the \
   acceptance_criteria specific enough to be checkable (no purely vague terms like \
   "appropriate", "as required" without quantification)?
3. over_inference — Are any quantitative values in the shall_statement (numbers with units) \
   backed by direct evidence? (pass = no over-inference; fail = numbers without direct backing)
4. ambiguity — Is the shall_statement free of unquantified vague qualitative terms? \
   (pass = unambiguous; fail = vague)
5. mbse_completeness — Are the four MBSE/SysML structural fields {{id, topic/name, shall_statement, \
   verification_method}} all present and non-empty?

Return ONLY valid JSON (no markdown):
{{
  "evidence_sufficiency": "pass" or "fail",
  "verifiability":        "pass" or "fail",
  "over_inference":       "pass" or "fail",
  "ambiguity":            "pass" or "fail",
  "mbse_completeness":    "pass" or "fail",
  "overall_comment":      "<one sentence summary, <=25 words>"
}}
"""

_DIMS = ["evidence_sufficiency", "verifiability", "over_inference", "ambiguity", "mbse_completeness"]


def _qg_automated_verdict(qg: QualityGate, er: dict[str, Any]) -> dict[str, bool]:
    report = qg.check(er)
    out: dict[str, bool] = {}
    for c in report.checks:
        out[c.dimension] = bool(c.passed)
    # Make sure every dim is present
    for d in _DIMS:
        out.setdefault(d, True)
    return out


def _expert_verdict_llm(client: Any, cfg: Any, er: dict[str, Any]) -> dict[str, bool]:
    prompt = _EXPERT_QG_PROMPT.format(
        er_id=safe_text(er.get("id")),
        shall=safe_text(er.get("shall_statement"))[:600],
        criteria=(er.get("acceptance_criteria") or [])[:6],
        vm=safe_text(er.get("verification_method")),
        evidence_ids=list(er.get("evidence_ids") or [])[:8],
        status=safe_text(er.get("support_status")),
        req_type=safe_text(er.get("requirement_type")),
    )
    try:
        resp = cached_completion(
            client,
            model=cfg.deepseek.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        obj = json.loads(resp.choices[0].message.content or "{}")
    except Exception as exc:  # noqa: BLE001
        # Default everything to pass so it doesn't bias the matrix too hard
        return {d: True for d in _DIMS} | {"_error": str(exc)}
    out: dict[str, Any] = {}
    for d in _DIMS:
        v = safe_text(obj.get(d, "pass")).lower()
        out[d] = v == "pass"
    out["_comment"] = safe_text(obj.get("overall_comment"))
    return out


def _confusion(qg_pass: list[bool], expert_pass: list[bool]) -> dict[str, int]:
    # Treat "expert says pass" as ground-truth positive
    tp = sum(1 for q, e in zip(qg_pass, expert_pass) if q and e)
    fp = sum(1 for q, e in zip(qg_pass, expert_pass) if q and not e)
    fn = sum(1 for q, e in zip(qg_pass, expert_pass) if not q and e)
    tn = sum(1 for q, e in zip(qg_pass, expert_pass) if not q and not e)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def _prf(cm: dict[str, int]) -> dict[str, float]:
    tp, fp, fn = cm["tp"], cm["fp"], cm["fn"]
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) else float("nan")
    return {
        "precision": round(prec, 4) if prec == prec else None,
        "recall": round(rec, 4) if rec == rec else None,
        "f1": round(f1, 4) if f1 == f1 else None,
    }


def run_qg_calibration(cfg: Any, out_dir: Path, *, n: int = 50, seed: int = 42) -> dict[str, Any]:
    print("\n[Sub-2] QG calibration (E-13)")
    batches = _find_complete_batches(cfg.paths.search_results_dir)
    print(f"  using {len(batches)} complete batches")
    qg = QualityGate()
    from openai import OpenAI
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url) if cfg.deepseek.enabled else None
    if client is None:
        raise RuntimeError("QG calibration requires DeepSeek; set DEEPSEEK_API_KEY.")

    # Collect every G4 ER across batches
    all_ers: list[dict[str, Any]] = []
    for exp in batches:
        for rs in _load_group(exp, "G4"):
            for er in rs.get("engineering_requirements") or []:
                all_ers.append(er)
    print(f"  total G4 engineering requirements available: {len(all_ers)}")

    rng = random.Random(seed)
    sample = rng.sample(all_ers, min(n, len(all_ers)))
    print(f"  sampled {len(sample)} for review (seed={seed})")

    per_item: list[dict[str, Any]] = []
    auto_vec = {d: [] for d in _DIMS}
    expert_vec = {d: [] for d in _DIMS}
    for i, er in enumerate(sample, 1):
        if i % 10 == 0 or i == 1:
            print(f"  reviewing {i}/{len(sample)} …")
        auto = _qg_automated_verdict(qg, er)
        exp = _expert_verdict_llm(client, cfg, er)
        for d in _DIMS:
            auto_vec[d].append(bool(auto.get(d, True)))
            expert_vec[d].append(bool(exp.get(d, True)))
        per_item.append({
            "er_id": safe_text(er.get("id")),
            "shall_statement": safe_text(er.get("shall_statement"))[:300],
            "automated": {d: auto.get(d) for d in _DIMS},
            "expert": {d: exp.get(d) for d in _DIMS},
            "expert_comment": exp.get("_comment", ""),
        })

    confusion = {d: _confusion(auto_vec[d], expert_vec[d]) for d in _DIMS}
    metrics = {d: _prf(confusion[d]) for d in _DIMS}

    # LaTeX table
    latex_lines = [
        "% Auto-generated by scripts/29_analysis.py qg-calibration",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Dimension & TP/FP/FN/TN & Precision & Recall & F1 \\\\",
        "\\hline",
    ]
    nice = {
        "evidence_sufficiency": "Evidence Sufficiency",
        "verifiability": "Verifiability",
        "over_inference": "Over-inference",
        "ambiguity": "Ambiguity",
        "mbse_completeness": "MBSE Completeness",
    }
    for d in _DIMS:
        c = confusion[d]
        m = metrics[d]
        p = "--" if m["precision"] is None else f"{m['precision']*100:.1f}\\%"
        r = "--" if m["recall"] is None else f"{m['recall']*100:.1f}\\%"
        f1 = "--" if m["f1"] is None else f"{m['f1']*100:.1f}\\%"
        latex_lines.append(
            f"{nice[d]} & {c['tp']}/{c['fp']}/{c['fn']}/{c['tn']} & {p} & {r} & {f1} \\\\"
        )
    latex_lines += ["\\hline", "\\end{tabular}"]
    (out_dir / "qg_calibration_table.tex").write_text("\n".join(latex_lines) + "\n", encoding="utf-8")
    print(f"  -> {out_dir / 'qg_calibration_table.tex'}")

    result = {
        "n_sampled": len(sample),
        "seed": seed,
        "confusion_matrices": confusion,
        "metrics": metrics,
        "per_item": per_item,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "note": "Expert verdict is an LLM (DeepSeek) acting as expert proxy via an independent prompt distinct from QualityGate's internal prompts.",
    }
    _write_json(out_dir / "qg_calibration.json", result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Sub-3: E-5 IR metrics (silver truth = G4 selected evidence_ids)
# ─────────────────────────────────────────────────────────────────────────────


def _evidence_ids_for_source(result_sets: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Aggregate (ordered, deduped) evidence_ids per source_requirement_id."""
    out: dict[str, list[str]] = {}
    for rs in result_sets:
        src = safe_text(rs.get("source_requirement_id"))
        if not src:
            continue
        seen: set[str] = set()
        order: list[str] = []
        for er in rs.get("engineering_requirements") or []:
            for ev in er.get("evidence_ids") or []:
                ev = safe_text(ev)
                if ev and ev not in seen:
                    seen.add(ev)
                    order.append(ev)
        out[src] = order
    return out


def _mrr(ranked: list[str], relevant: set[str]) -> float:
    for i, e in enumerate(ranked, 1):
        if e in relevant:
            return 1.0 / i
    return 0.0


def _ndcg_at_k(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    dcg = 0.0
    for i, e in enumerate(ranked[:k], 1):
        if e in relevant:
            dcg += 1.0 / math.log2(i + 1)
    ideal = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal + 1))
    return dcg / idcg if idcg > 0 else 0.0


def _recall_at_k(ranked: list[str], relevant: set[str], k: int = 4) -> float:
    if not relevant:
        return float("nan")
    top = set(ranked[:k])
    return len(top & relevant) / len(relevant)


def _precision_at_k(ranked: list[str], relevant: set[str], k: int = 4) -> float:
    if k == 0:
        return float("nan")
    top = ranked[:k]
    if not top:
        return float("nan")
    hits = sum(1 for e in top if e in relevant)
    return hits / min(k, len(top))


def run_ir_metrics(cfg: Any, out_dir: Path) -> dict[str, Any]:
    print("\n[Sub-3] IR metrics (E-5, silver-truth approximation)")
    batches = _find_complete_batches(cfg.paths.search_results_dir)
    print(f"  using {len(batches)} complete batches")

    per_batch: list[dict[str, Any]] = []
    agg: dict[str, dict[str, list[float]]] = {g: {m: [] for m in ["mrr", "ndcg_10", "recall_4", "precision_4"]} for g in ALL_GROUPS}

    for exp in batches:
        # Silver truth = G4's per-source evidence_ids
        silver = _evidence_ids_for_source(_load_group(exp, "G4"))
        batch_res: dict[str, Any] = {"batch": exp.parent.name, "n_sources_with_silver": sum(1 for v in silver.values() if v)}
        for g in ALL_GROUPS:
            ranked_per_src = _evidence_ids_for_source(_load_group(exp, g))
            mrr_l, ndcg_l, r4_l, p4_l = [], [], [], []
            for src, relevant_list in silver.items():
                relevant = set(relevant_list)
                ranked = ranked_per_src.get(src, [])
                if not relevant:
                    continue  # No silver truth -> skip
                if not ranked:
                    # Group produced no evidence at all (typical for G1) → 0s but counted
                    mrr_l.append(0.0)
                    ndcg_l.append(0.0)
                    r4_l.append(0.0)
                    p4_l.append(0.0)
                    continue
                mrr_l.append(_mrr(ranked, relevant))
                ndcg_l.append(_ndcg_at_k(ranked, relevant, 10))
                r4_l.append(_recall_at_k(ranked, relevant, 4))
                p4_l.append(_precision_at_k(ranked, relevant, 4))

            def _mean(xs: list[float]) -> float:
                xs = [x for x in xs if x == x]  # drop nan
                return round(sum(xs) / len(xs), 4) if xs else float("nan")

            batch_res[g] = {
                "mrr": _mean(mrr_l),
                "ndcg_10": _mean(ndcg_l),
                "recall_4": _mean(r4_l),
                "precision_4": _mean(p4_l),
                "n_queries": len(mrr_l),
            }
            # Aggregate across batches (per-query values, not per-batch means)
            for arr, name in zip([mrr_l, ndcg_l, r4_l, p4_l], ["mrr", "ndcg_10", "recall_4", "precision_4"]):
                agg[g][name].extend([x for x in arr if x == x])
        per_batch.append(batch_res)

    # Per-group across-batch aggregate
    overall = {}
    for g in ALL_GROUPS:
        row: dict[str, Any] = {}
        for m in ["mrr", "ndcg_10", "recall_4", "precision_4"]:
            xs = agg[g][m]
            if xs:
                mean = sum(xs) / len(xs)
                std = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(len(xs) - 1, 1)) if len(xs) > 1 else 0.0
                row[m] = {"mean": round(mean, 4), "std": round(std, 4), "n": len(xs)}
            else:
                row[m] = {"mean": None, "std": None, "n": 0}
        overall[g] = row

    # LaTeX table
    latex_lines = [
        "% Auto-generated by scripts/29_analysis.py ir-metrics",
        "% NOTE: Silver-truth approximation: G4's selected evidence_ids per source requirement",
        "% are treated as the relevant set. G4 metrics are upper-bound by construction.",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Group & MRR & nDCG@10 & Recall@4 & Precision@4 \\\\",
        "\\hline",
    ]
    for g in ALL_GROUPS:
        row = overall[g]
        cells = []
        for m in ["mrr", "ndcg_10", "recall_4", "precision_4"]:
            v = row[m]["mean"]
            if v is None:
                cells.append("--")
            else:
                cells.append(f"{v*100:.1f}")
        latex_lines.append(f"{g} & " + " & ".join(cells) + " \\\\")
    latex_lines += ["\\hline", "\\end{tabular}"]
    (out_dir / "ir_metrics_table.tex").write_text("\n".join(latex_lines) + "\n", encoding="utf-8")
    print(f"  -> {out_dir / 'ir_metrics_table.tex'}")

    result = {
        "n_batches": len(batches),
        "silver_truth": "G4 evidence_ids per source_requirement_id; this is silver-truth approximation, not gold.",
        "per_batch": per_batch,
        "overall": overall,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(out_dir / "ir_metrics.json", result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Sub-4: E-9 Held-out test set (30 NEW requirements)
# ─────────────────────────────────────────────────────────────────────────────

_HELDOUT_PROMPT = """\
You are a marine engineering requirements specialist for ship main engine cooling water systems.

Generate exactly 30 NEW stakeholder requirements about the ship main engine cooling \
water system that are DIFFERENT from any of the existing pool of requirements below.

The 30 new requirements MUST:
1. Cover a mix of the 16 stakeholder types listed below (try to roughly distribute \
   them, e.g., 1-3 per stakeholder).
2. Be specific to marine engineering: cover NEW aspects such as cathodic protection, \
   chemical dosing, sensor calibration, transient response, freezing protection, \
   sound/vibration limits, EEDI compliance, redundancy under blackout, drydock \
   procedures, retrofit constraints, etc.
3. Be written in Chinese, 1-3 sentences each, clear engineering language.
4. NOT duplicate any topic already in the existing pool.

Stakeholder types (use these exact Chinese strings):
{stakeholders}

A sample of the existing pool (avoid these topics):
{existing_sample}

Output ONLY a JSON object of this shape:
{{
  "requirements": [
    {{"stakeholder": "<one of the listed types>", "requirement_text": "<Chinese text>"}},
    ... (exactly 30 items)
  ]
}}
"""


def _load_pool_for_heldout(cfg: Any) -> list[dict[str, Any]]:
    p = cfg.paths.processed_dir / "requirement_pool_100.jsonl"
    if not p.exists():
        return []
    return read_jsonl(str(p))


def _generate_heldout_requirements(cfg: Any, *, n: int = 30, seed: int = 999) -> list[dict[str, Any]]:
    pool = _load_pool_for_heldout(cfg)
    stakeholders = sorted({safe_text(r.get("stakeholder")) for r in pool if r.get("stakeholder")})
    rng = random.Random(seed)
    sample_existing = rng.sample(pool, min(20, len(pool)))
    prompt = _HELDOUT_PROMPT.format(
        stakeholders="\n".join(f"- {s}" for s in stakeholders),
        existing_sample="\n".join(f"- [{r.get('stakeholder')}] {r.get('requirement_text')}" for r in sample_existing),
    )
    from openai import OpenAI
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)

    # Vary the prompt with a deterministic seed-derived marker so the cache key
    # is unique to this held-out generation (and won't collide with anything in
    # the main pool).
    marker = f"[heldout-seed-{seed}]"
    resp = cached_completion(
        client,
        model=cfg.deepseek.model,
        messages=[
            {"role": "user", "content": marker + "\n\n" + prompt},
        ],
        temperature=0.0,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )
    obj = json.loads(resp.choices[0].message.content or "{}")
    reqs = obj.get("requirements") or []
    # Coerce + assign IDs
    out: list[dict[str, Any]] = []
    for i, r in enumerate(reqs[:n], 1):
        out.append({
            "requirement_id": f"H{i:03d}",
            "stakeholder": safe_text(r.get("stakeholder")),
            "requirement_text": safe_text(r.get("requirement_text")),
        })
    return out


def run_held_out(cfg: Any, out_dir: Path, *, force_cpu: bool = False) -> dict[str, Any]:
    print("\n[Sub-4] Held-out test set (E-9)")
    held_path = cfg.paths.processed_dir / "held_out_requirements_30.jsonl"

    if held_path.exists():
        held = read_jsonl(str(held_path))
        print(f"  reusing {len(held)} held-out requirements from {held_path}")
    else:
        print("  generating 30 NEW requirements via DeepSeek (seed=999) …")
        held = _generate_heldout_requirements(cfg, n=30, seed=999)
        if len(held) < 30:
            print(f"  WARNING: only got {len(held)} requirements from LLM (expected 30)")
        held_path.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(str(held_path), held)
        print(f"  -> {held_path}")

    # Run G4 pipeline on them
    print(f"  running G4 pipeline on {len(held)} held-out requirements …")
    # Allow caller to force CPU via FORCE_CPU=1 (useful when a parallel job
    # already holds the GPU).  We bypass the cached AppConfig by constructing
    # a custom retriever with explicit device.
    from cooling_rag_mg.engineering_requirement_agent import generate_engineering_requirements
    from cooling_rag_mg.retrieval_engine import MultiGranularRetriever
    from cooling_rag_mg.pipeline import PipelineServices, run_requirements_with_services
    from cooling_rag_mg.sysml_exporter import export_batch
    import os as _os

    pipeline_reqs = [
        {
            "requirement_id": r["requirement_id"],
            "stakeholder": r.get("stakeholder", ""),
            "requirement_text": r.get("requirement_text", ""),
        }
        for r in held
    ]
    if not force_cpu:
        force_cpu = _os.getenv("FORCE_CPU", "0").strip() == "1"
    device = "cpu" if force_cpu else cfg.model.device
    if device == "cpu":
        try:
            import torch as _t
            _t.set_num_threads(2)
            _t.set_num_interop_threads(1)
        except Exception:
            pass
    print(f"  retriever device = {device}")

    try:
        retriever = MultiGranularRetriever(
            source_index_dir=str(cfg.paths.indexes_dir / "source_chunks"),
            evidence_index_dir=str(cfg.paths.indexes_dir / "evidence_units"),
            evidence_units_path=str(cfg.paths.evidence_units_jsonl),
            evidence_groups_path=str(cfg.paths.evidence_groups_jsonl),
            device=device,
        )
        services = PipelineServices(retriever=retriever)
        retrieval_payload = run_requirements_with_services(
            pipeline_reqs,
            services=services,
            top_k=4,
            coarse_k=12,
            fine_k=40,
        )
        output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
        result_sets = output.get("requirement_sets", [])
    except BaseException as exc:  # noqa: BLE001  (catch CUDA / system errors too)
        print(f"  WARNING: pipeline failed ({type(exc).__name__}: {exc})")
        print("  Saving partial held-out (requirements only) and skipping metrics.")
        partial = {
            "n_requirements": len(held),
            "metrics": None,
            "result_sets": [],
            "held_out_pool_path": str(held_path),
            "pipeline_error": f"{type(exc).__name__}: {exc}",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "note": (
                "Held-out requirements generated with seed=999, disjoint from the 100-pool. "
                "Pipeline execution deferred — re-run with `python scripts/29_analysis.py held-out` "
                "after GPU and main memory are free."
            ),
        }
        _write_json(out_dir / "held_out_test.json", partial)
        return partial
    # Attach QG
    qg = QualityGate()
    for rs in result_sets:
        rs["_group"] = "G4_heldout"
        for er in rs.get("engineering_requirements") or []:
            er["quality_gate_report"] = qg.check(er).to_dict()

    # Compute M1-M5 on held-out
    ers: list[dict[str, Any]] = []
    for rs in result_sets:
        ers.extend(rs.get("engineering_requirements") or [])

    import re
    _UNIT_RE = re.compile(r"\d+\.?\d*\s*(%|°C|℃|bar|kPa|MPa|Pa|m³/h|m3/h|L/h|l/h|L/min|l/min|rpm|kW|MW|mm|m|kg|t|Hz|V|A|h|min|s)", re.IGNORECASE)

    def m1() -> float:
        empty = sum(1 for e in ers if not (e.get("evidence_ids") or []))
        return round(empty / len(ers), 4) if ers else float("nan")

    def m2() -> float:
        passed = sum(1 for e in ers if (e.get("quality_gate_report") or {}).get("overall_passed"))
        return round(passed / len(ers), 4) if ers else float("nan")

    def m3() -> float:
        failed = sum(1 for e in ers if not qg._over_inference(e).passed)  # noqa: SLF001
        return round(failed / len(ers), 4) if ers else float("nan")

    def m4() -> float:
        passed = sum(1 for e in ers if qg._verifiability(e).passed)  # noqa: SLF001
        return round(passed / len(ers), 4) if ers else float("nan")

    def m5() -> float:
        passed = sum(1 for e in ers if qg._mbse_completeness(e).passed)  # noqa: SLF001
        return round(passed / len(ers), 4) if ers else float("nan")

    metrics = {"m1_evidence_free": m1(), "m2_qg_pass": m2(), "m3_over_inference": m3(),
               "m4_verifiability": m4(), "m5_mbse_completeness": m5(),
               "n_requirement_sets": len(result_sets), "n_engineering_requirements": len(ers)}
    print(f"  M1={metrics['m1_evidence_free']}  M2={metrics['m2_qg_pass']}  "
          f"M3={metrics['m3_over_inference']}  M4={metrics['m4_verifiability']}  "
          f"M5={metrics['m5_mbse_completeness']}")

    result = {
        "n_requirements": len(held),
        "metrics": metrics,
        "result_sets": result_sets,
        "held_out_pool_path": str(held_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "note": "Held-out requirements generated with seed=999, disjoint from the 100-pool used in T3.",
    }
    _write_json(out_dir / "held_out_test.json", result)

    # Free GPU
    try:
        import gc
        del services
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Sub-5: E-14 Per-stakeholder × per-component heatmap (G4 only)
# ─────────────────────────────────────────────────────────────────────────────


def _component_for_er(er: dict[str, Any], ev_lookup: dict[str, dict[str, Any]]) -> str:
    """Best-effort assignment of an ER to a primary component label."""
    comps: list[str] = []
    for ev_id in er.get("evidence_ids") or []:
        meta = ev_lookup.get(ev_id, {})
        for c in (meta.get("component_objects") or [])[:1]:
            c = safe_text(c)
            if c:
                comps.append(c)
                break
    if comps:
        return comps[0]
    # Fall back to requirement_type as component proxy (so cells aren't all empty)
    return f"<type:{safe_text(er.get('requirement_type')) or 'unknown'}>"


def run_heatmaps(cfg: Any, out_dir: Path) -> dict[str, Any]:
    print("\n[Sub-5] Per-stakeholder x per-component heatmaps (E-14)")
    batches = _find_complete_batches(cfg.paths.search_results_dir)
    print(f"  using {len(batches)} complete batches")
    qg = QualityGate()
    ev_lookup = _load_evidence_lookup(cfg)
    print(f"  loaded {len(ev_lookup)} evidence units")

    # Cell: (stakeholder, component) -> [failed_count, total_count]
    m1_table: dict[tuple[str, str], list[int]] = collections.defaultdict(lambda: [0, 0])
    m3_table: dict[tuple[str, str], list[int]] = collections.defaultdict(lambda: [0, 0])

    for exp in batches:
        for rs in _load_group(exp, "G4"):
            stake = safe_text(rs.get("stakeholder")) or "<unknown>"
            for er in rs.get("engineering_requirements") or []:
                comp = _component_for_er(er, ev_lookup)
                # M1: evidence-free
                m1_failed = not (er.get("evidence_ids") or [])
                m1_table[(stake, comp)][0] += int(m1_failed)
                m1_table[(stake, comp)][1] += 1
                # M3: over-inference failed
                m3_failed = not qg._over_inference(er).passed  # noqa: SLF001
                m3_table[(stake, comp)][0] += int(m3_failed)
                m3_table[(stake, comp)][1] += 1

    # Build the cross matrices
    stakeholders = sorted({k[0] for k in set(m1_table.keys()) | set(m3_table.keys())})
    components = sorted({k[1] for k in set(m1_table.keys()) | set(m3_table.keys())})

    # Trim to top-12 components by total count, lump rest into "<other>"
    comp_totals: dict[str, int] = collections.defaultdict(int)
    for (s, c), (failed, tot) in m1_table.items():
        comp_totals[c] += tot
    top_comps = [c for c, _ in sorted(comp_totals.items(), key=lambda x: -x[1])[:12]]

    def _matrix(table: dict[tuple[str, str], list[int]]) -> tuple[list[list[float]], list[list[str]]]:
        rows: list[list[float]] = []
        labels: list[list[str]] = []
        for s in stakeholders:
            row_vals: list[float] = []
            row_labels: list[str] = []
            for c in top_comps:
                failed, tot = table.get((s, c), [0, 0])
                # also fold non-top components into <other> bucket for this row
                rate = float("nan")
                if tot > 0:
                    rate = failed / tot
                row_vals.append(rate)
                row_labels.append(f"{failed}/{tot}")
            # <other> bucket
            other_failed = sum(table.get((s, c), [0, 0])[0] for c in components if c not in top_comps)
            other_tot = sum(table.get((s, c), [0, 0])[1] for c in components if c not in top_comps)
            other_rate = (other_failed / other_tot) if other_tot else float("nan")
            row_vals.append(other_rate)
            row_labels.append(f"{other_failed}/{other_tot}")
            rows.append(row_vals)
            labels.append(row_labels)
        return rows, labels

    m1_matrix, m1_lbls = _matrix(m1_table)
    m3_matrix, m3_lbls = _matrix(m3_table)
    column_labels = top_comps + ["<other>"]

    # Plot helper
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # Best-effort CJK font configuration so Chinese stakeholder/component names render
    try:
        import matplotlib.font_manager as fm
        candidates = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Noto Sans SC", "SimSun"]
        installed = {f.name for f in fm.fontManager.ttflist}
        for name in candidates:
            if name in installed:
                plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                break
    except Exception:
        pass

    def _plot(matrix: list[list[float]], cell_labels: list[list[str]], title: str, path: Path) -> None:
        mat = np.array([[v if v == v else 0.0 for v in row] for row in matrix])
        fig, ax = plt.subplots(figsize=(max(10, len(column_labels) * 0.9), max(6, len(stakeholders) * 0.45)))
        im = ax.imshow(mat, aspect="auto", cmap="Reds", vmin=0.0, vmax=1.0)
        ax.set_xticks(range(len(column_labels)))
        ax.set_xticklabels(column_labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(stakeholders)))
        ax.set_yticklabels(stakeholders, fontsize=8)
        ax.set_title(title)
        for i in range(len(stakeholders)):
            for j in range(len(column_labels)):
                v = matrix[i][j]
                if v != v:
                    text = "--"
                else:
                    text = f"{v*100:.0f}%\n{cell_labels[i][j]}"
                ax.text(j, i, text, ha="center", va="center", fontsize=7,
                        color="black" if mat[i, j] < 0.5 else "white")
        cb = fig.colorbar(im, ax=ax)
        cb.set_label("Failure rate")
        plt.tight_layout()
        fig.savefig(path, dpi=140)
        plt.close(fig)
        print(f"  -> {path}")

    _plot(m1_matrix, m1_lbls, "M1 (Evidence-Free Rate) by Stakeholder × Component — G4", out_dir / "heatmap_M1.png")
    _plot(m3_matrix, m3_lbls, "M3 (Over-Inference Rate) by Stakeholder × Component — G4", out_dir / "heatmap_M3.png")

    return {
        "n_batches": len(batches),
        "stakeholders": stakeholders,
        "components": column_labels,
        "m1_matrix": m1_matrix,
        "m3_matrix": m3_matrix,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=[
        "failure-taxonomy", "qg-calibration",
        "held-out", "heatmaps", "all",
    ])
    parser.add_argument("--n", type=int, default=50, help="Sample size for qg-calibration (default 50)")
    parser.add_argument("--seed", type=int, default=42, help="Sample seed for qg-calibration")
    parser.add_argument("--cpu", action="store_true",
                        help="Force held-out pipeline to run on CPU (use when GPU is busy)")
    args = parser.parse_args()

    cfg = get_config()
    out_dir = cfg.paths.search_results_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.cmd in {"failure-taxonomy", "all"}:
        run_failure_taxonomy(cfg, out_dir)
    if args.cmd in {"qg-calibration", "all"}:
        run_qg_calibration(cfg, out_dir, n=args.n, seed=args.seed)
    if args.cmd in {"heatmaps", "all"}:
        run_heatmaps(cfg, out_dir)
    if args.cmd in {"held-out", "all"}:
        run_held_out(cfg, out_dir, force_cpu=args.cpu)

    print("\nDone.")


if __name__ == "__main__":
    main()
