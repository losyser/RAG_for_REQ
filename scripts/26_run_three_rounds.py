# -*- coding: utf-8 -*-
"""
Script 26: Run 3 rounds of the 6-group experiment, each time randomly sampling
30 requirements from the 100-requirement pool (data/processed/requirement_pool_100.jsonl).

Each round produces a separate batch_* directory. At the end, aggregated
metrics (mean +/- std) are printed and saved to data/search_results/three_round_summary.json.

Prerequisites:
  python scripts/25_generate_requirement_pool.py   # build the 100-req pool

Usage:
  python scripts/26_run_three_rounds.py [--top-k 4] [--seeds 42 7 99]
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg import seed_everything
from cooling_rag_mg.config import get_config
from cooling_rag_mg.engineering_requirement_agent import (
    ENGINEERING_REQUIREMENT_PROMPT,
    generate_engineering_requirements,
)
from cooling_rag_mg.evidence_pack import make_batch_dir
from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
from cooling_rag_mg.llm_cache import cached_completion, cache_stats
from cooling_rag_mg.pipeline import make_services, run_requirements_with_services
from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.sysml_exporter import export_batch
from cooling_rag_mg.text_utils import safe_text

ALL_GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]


def _free_gpu() -> None:
    """Release GPU memory between groups to avoid OOM when loading new models."""
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def _to_pipeline_input(reqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": r["requirement_id"],
            "stakeholder": r.get("stakeholder", ""),
            "requirement_text": r.get("requirement_text", ""),
        }
        for r in reqs
    ]


# ── G1 (paired baseline: same prompt as G2-G4 but empty retrieval context) ───

_G1_USER_MARKER = (
    "This is a no-evidence baseline; produce shall statements based on the "
    "requirement text alone. Do not fabricate evidence_ids — leave evidence_ids "
    "empty for every engineering requirement. Set support_status to "
    "'no_evidence_baseline'. Do not invent specific quantitative values; use "
    "the standard placeholders defined in the prompt (e.g., '按主机厂家 "
    "Technical Data 确认')."
)


def _run_g1_local(
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
) -> list[dict[str, Any]]:
    """G1 paired baseline.

    Uses the SAME system prompt as G2-G4 (ENGINEERING_REQUIREMENT_PROMPT) but
    feeds an empty retrieval_context.supported_evidence so the only difference
    from the proposed pipeline is the absence of retrieval evidence.
    """
    from openai import OpenAI
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
    results = []
    for r in reqs:
        try:
            payload = {
                "original_requirement": {
                    "requirement_id": r["requirement_id"],
                    "stakeholder": r.get("stakeholder", ""),
                    "raw_requirement_text": r.get("requirement_text", ""),
                },
                "retrieval_context": {
                    "requirement_id": r["requirement_id"],
                    "stakeholder": r.get("stakeholder", ""),
                    "raw_requirement_text": r.get("requirement_text", ""),
                    "supported_evidence": [],
                    "supported_evidence_by_topic": {},
                    "background_evidence_for_reference_only": [],
                    "evidence_gap_summary": [],
                    "allowed_engineering_aspects": [],
                    "sub_requirement_type_distribution": {},
                    "generation_basis": "no_evidence_baseline",
                },
                "no_evidence_baseline": True,
            }
            resp = cached_completion(
                client,
                model=cfg.deepseek.model,
                messages=[
                    {"role": "system", "content": ENGINEERING_REQUIREMENT_PROMPT},
                    {"role": "user", "content": _G1_USER_MARKER},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=cfg.deepseek.temperature,
                max_tokens=cfg.deepseek.max_tokens_requirement_agent,
                response_format={"type": "json_object"},
            )
            obj = json.loads(resp.choices[0].message.content or "{}")
            # Enforce baseline invariants (defensive: model may have ignored)
            obj["_group"] = "G1"
            obj["generation_basis"] = "no_evidence_baseline"
            obj.setdefault("source_requirement_id", r["requirement_id"])
            obj.setdefault("stakeholder", r.get("stakeholder", ""))
            for er in obj.get("engineering_requirements", []) or []:
                er["evidence_ids"] = []
                er["support_status"] = "no_evidence_baseline"
            results.append(obj)
            print(f"  [G1] {r['requirement_id']} OK")
        except Exception as exc:
            print(f"  [G1] {r['requirement_id']} FAIL {exc}")
    return results


def _build_flat_retrieval_payload_local(
    reqs: list[dict[str, Any]],
    cfg: Any,
    top_k: int,
    services: Any,
) -> dict[str, Any]:
    from cooling_rag_mg.evidence_judge import apply_judge
    from cooling_rag_mg.hybrid_fusion import rrf_fuse
    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index

    # Reuse the shared model from services.retriever — no extra GPU load
    shared_model = services.retriever.evidence_searcher.model
    searcher = HybridIndexSearcher(
        load_index(str(cfg.paths.indexes_dir / "evidence_units")),
        device=cfg.model.device,
        model=shared_model,
    )
    requirement_results = []
    for r in reqs:
        req_id = r["requirement_id"]
        req_text = r.get("requirement_text", "")
        stakeholder = r.get("stakeholder", "")

        # Use the LLM splitter so that G2→G3 isolates multi-granularity only.
        # Without splitting, G2 vs G3 conflates two variables (granularity + splitting).
        # Falls back to a single synthetic sub if the splitter is unavailable.
        try:
            sub_reqs = services.splitter(req_id, stakeholder, req_text)
        except Exception:
            sub_reqs = [{
                "sub_requirement_id": f"{req_id}-01",
                "requirement_type": "other",
                "topic": req_text[:40],
                "text": req_text,
            }]

        sub_results = []
        for sub in sub_reqs:
            query = sub.get("text", req_text)
            vec = searcher.vector_search(query, top_k * 6)
            bm25 = searcher.bm25_search(query, top_k * 6)
            candidates = rrf_fuse([vec, bm25])
            applicable, _ = services.applicability_filter.apply(
                sub, candidates, top_k_for_judge=top_k * 3,
            )
            judge_result = services.judge(sub, applicable, max_selected=top_k)
            selected, _ = apply_judge(applicable, judge_result)
            sub_results.append({
                **sub,
                "selected_results": selected,
                "evidence_gap": None,
                "stage_diagnostics": {"judge_method": judge_result.get("judge_method", "")},
            })

        requirement_results.append({
            "requirement_id": req_id,
            "stakeholder": stakeholder,
            "raw_requirement_text": req_text,
            "sub_requirements": sub_results,
        })
    del searcher
    _free_gpu()
    return {"requirements": requirement_results, "diagnostics": {}}


def _attach_judge_methods(
    results: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Carry stage_diagnostics.judge_method from pipeline into the saved JSON.

    The agent's engineering_requirements output collapses sub_requirements,
    so we attach a per-set `_judge_methods` field listing the judge_method
    used at each sub_requirement of the originating requirement.  This makes
    it possible to audit, post-hoc, whether a given engineering requirement
    was produced from LLM-judged vs fallback-judged evidence.
    """
    by_id: dict[str, dict[str, Any]] = {}
    for r in retrieval_payload.get("requirements", []) or []:
        rid = safe_text(r.get("requirement_id"))
        if rid:
            by_id[rid] = r

    for rs in results:
        src_id = safe_text(rs.get("source_requirement_id"))
        ctx = by_id.get(src_id, {})
        per_sub = []
        for sub in ctx.get("sub_requirements", []) or []:
            diag = sub.get("stage_diagnostics", {}) or {}
            per_sub.append({
                "sub_requirement_id": safe_text(sub.get("sub_requirement_id")),
                "topic": safe_text(sub.get("topic")),
                "judge_method": safe_text(diag.get("judge_method")),
            })
        rs["_judge_methods"] = per_sub
    return results


def _attach_quality_gate_local(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qg = QualityGate()
    for rs in results:
        eng_reqs = rs.get("engineering_requirements") or []
        for er in eng_reqs:
            report = qg.check(er)
            er["quality_gate_report"] = report.to_dict()
        passed = sum(
            1 for er in eng_reqs
            if (er.get("quality_gate_report") or {}).get("overall_passed")
        )
        rs["_quality_gate_summary"] = {
            "total": len(eng_reqs),
            "passed": passed,
            "avg_score": (
                sum((er.get("quality_gate_report") or {}).get("score", 0) for er in eng_reqs)
                / max(len(eng_reqs), 1)
            ),
        }
    return results


def _disable_profile_scoring_local(retriever: Any) -> None:
    def _flat_score(items: list[dict], profile: dict, *, is_chunk: bool = False) -> list[dict]:
        for item in items:
            item["profile_score"] = 0.0
            item["final_score"] = float(item.get("rrf_score", 0.0))
        return items

    def _flat_filter(items: list[dict], profile: dict) -> list[dict]:
        from cooling_rag_mg.schema import normalize_v2_metadata
        out = []
        for item in items:
            meta = normalize_v2_metadata(item.get("metadata", {}) or {})
            if safe_text(meta.get("evidence_strength")).lower() == "not_applicable":
                continue
            if meta.get("is_noise") is True:
                continue
            item["retrieval_role"] = item.get("retrieval_role") or "candidate"
            item["metadata"] = meta
            out.append(item)
        return out

    retriever._score_by_profile = _flat_score      # type: ignore[method-assign]
    retriever._soft_filter_by_profile = _flat_filter  # type: ignore[method-assign]


def _run_g2_local(
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
    top_k: int,
    services: Any,
) -> list[dict[str, Any]]:
    pipeline_reqs = _to_pipeline_input(reqs)
    retrieval_payload = _build_flat_retrieval_payload_local(reqs, cfg, top_k, services)
    output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
    results = []
    for rs in output.get("requirement_sets", []):
        rs["_group"] = "G2"
        results.append(rs)
        print(f"  [G2] {rs.get('source_requirement_id')} OK")
    results = _attach_judge_methods(results, retrieval_payload)
    return results


def _run_pipeline_group_local(
    group: str,
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
    *,
    with_quality_gate: bool,
    with_profile_scoring: bool,
    top_k: int,
    services: Any,
) -> list[dict[str, Any]]:
    pipeline_reqs = _to_pipeline_input(reqs)

    if not with_profile_scoring:
        _disable_profile_scoring_local(services.retriever)

    retrieval_payload = run_requirements_with_services(
        pipeline_reqs,
        services=services,
        top_k=top_k,
        coarse_k=12,
        fine_k=40,
    )
    output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
    results = []
    for rs in output.get("requirement_sets", []):
        rs["_group"] = group
        results.append(rs)
        print(f"  [{group}] {rs.get('source_requirement_id')} OK")

    results = _attach_judge_methods(results, retrieval_payload)

    if with_quality_gate:
        results = _attach_quality_gate_local(results)

    if group == "G4":
        xml_dir = exp_dir / "G4_sysml_xml"
        export_batch(results, xml_dir)
        print(f"  [G4] SysML XML -> {xml_dir}")

    return results


# ── 指标计算 ──────────────────────────────────────────────────────────────────

def _flatten_ers(result_sets: list[dict]) -> list[dict]:
    out = []
    for rs in result_sets:
        for er in (rs.get("engineering_requirements") or []):
            out.append(dict(er))
    return out


def _compute_metrics(
    exp_dir: Path,
    groups: list[str],
    qg: QualityGate,
) -> list[dict[str, Any]]:
    import re
    _UNIT_RE = re.compile(
        r"\d+\.?\d*\s*"
        r"(%|°C|℃|bar|kPa|MPa|Pa|m³/h|m3/h|L/h|l/h|L/min|l/min"
        r"|rpm|kW|MW|mm(?![a-zA-Z])|m(?![a-zA-Z])|kg(?![a-zA-Z])|t(?![a-zA-Z])"
        r"|Hz|V(?![a-zA-Z])|A(?![a-zA-Z])|h(?![a-zA-Z])|min(?![a-zA-Z])|s(?![a-zA-Z]))",
        re.IGNORECASE,
    )

    rows = []
    for group in groups:
        path = exp_dir / f"{group}_results.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rsets = data["result_sets"] if isinstance(data, dict) else data
        ers = _flatten_ers(rsets)
        if not ers:
            continue

        def m1():
            if group == "G1":
                return float("nan")
            empty = sum(1 for e in ers if not (e.get("evidence_ids") or []))
            return round(empty / len(ers), 4)

        def m2():
            if group not in {"G4", "A2"}:
                return float("nan")
            qg_ers = [e for e in ers if e.get("quality_gate_report")]
            if not qg_ers:
                return float("nan")
            passed = sum(1 for e in qg_ers if (e.get("quality_gate_report") or {}).get("overall_passed"))
            return round(passed / len(qg_ers), 4)

        def m3():
            failed = sum(1 for e in ers if not qg._over_inference(e).passed)  # noqa: SLF001
            return round(failed / len(ers), 4)

        def m4():
            passed = sum(1 for e in ers if qg._verifiability(e).passed)  # noqa: SLF001
            return round(passed / len(ers), 4)

        def m5():
            if group == "G1":
                return float("nan")
            passed = sum(1 for e in ers if qg._mbse_completeness(e).passed)  # noqa: SLF001
            return round(passed / len(ers), 4)

        rows.append({
            "group": group,
            "n_sets": len(rsets),
            "n_reqs": len(ers),
            "m1": m1(),
            "m2": m2(),
            "m3": m3(),
            "m4": m4(),
            "m5": m5(),
        })
    return rows


# ── 聚合统计 ──────────────────────────────────────────────────────────────────

def _aggregate(all_round_metrics: list[list[dict]]) -> list[dict]:
    """Compute mean +/- std across rounds for each group × metric."""
    groups = list({r["group"] for round_m in all_round_metrics for r in round_m})
    groups_order = ["G1", "G2", "G3", "G4", "A1", "A2"]
    groups = [g for g in groups_order if g in groups]

    summary = []
    for group in groups:
        vals: dict[str, list[float]] = {k: [] for k in ["m1", "m2", "m3", "m4", "m5"]}
        n_sets_list, n_reqs_list = [], []
        for round_m in all_round_metrics:
            for row in round_m:
                if row["group"] == group:
                    n_sets_list.append(row["n_sets"])
                    n_reqs_list.append(row["n_reqs"])
                    for k in vals:
                        v = row[k]
                        if v == v:  # not nan
                            vals[k].append(v)

        def stats(lst: list[float]) -> dict:
            if not lst:
                return {"mean": None, "std": None}
            mean = sum(lst) / len(lst)
            std = math.sqrt(sum((x - mean) ** 2 for x in lst) / max(len(lst) - 1, 1))
            return {"mean": round(mean, 4), "std": round(std, 4)}

        summary.append({
            "group": group,
            "n_rounds": len(all_round_metrics),
            "avg_n_sets": round(sum(n_sets_list) / max(len(n_sets_list), 1), 1),
            "avg_n_reqs": round(sum(n_reqs_list) / max(len(n_reqs_list), 1), 1),
            **{k: stats(vals[k]) for k in vals},
        })
    return summary


def _print_summary(summary: list[dict]) -> None:
    def fmt(s: dict | None) -> str:
        if s is None or s.get("mean") is None:
            return "   N/A  "
        return f"{s['mean']*100:4.1f}+/-{s['std']*100:3.1f}%"

    header = f"{'Group':<6} {'Rnd':>3} {'N_req':>6}  {'M1 EFR':>9} {'M2 QGP':>9} {'M3 OIR':>9} {'M4 VER':>9} {'M5 MBSE':>9}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))
    for row in summary:
        line = (
            f"{row['group']:<6} {row['n_rounds']:>3} {row['avg_n_reqs']:>6.0f}  "
            f"{fmt(row['m1']):>9} {fmt(row['m2']):>9} {fmt(row['m3']):>9} "
            f"{fmt(row['m4']):>9} {fmt(row['m5']):>9}"
        )
        print(line)
    print("=" * len(header))
    print(
        "\nM1=Evidence-Free Rate (down)  M2=QG Pass Rate (up)  M3=Over-Inference (down)\n"
        "M4=Verifiability (up)       M5=MBSE Completeness (up)   format: mean+/-std"
    )


# ── 单轮实验 ──────────────────────────────────────────────────────────────────

def _probe_model(cfg: Any) -> str:
    """Send a 1-token probe to the LLM endpoint and return the model id it reports.

    Used to record the actual upstream model alias (which may differ from the
    nominally requested one, e.g. when DeepSeek silently routes 'deepseek-chat'
    to 'deepseek-chat-v4' or similar).  Returns '' on failure so manifest
    writing never blocks a run.
    """
    if not cfg.deepseek.enabled:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
        # Probe through the cache so identical probes don't burn quota across runs.
        resp = cached_completion(
            client,
            model=cfg.deepseek.model,
            messages=[{"role": "user", "content": "ping"}],
            temperature=cfg.deepseek.temperature,
            max_tokens=5,
        )
        return getattr(resp, "model", "") or ""
    except Exception as exc:
        print(f"[probe] failed: {exc}")
        return ""


def _gather_package_versions() -> dict[str, str]:
    """Best-effort capture of relevant package versions for manifest.json."""
    import importlib.metadata as md
    pkgs = ["openai", "diskcache", "faiss-cpu", "rank-bm25", "torch", "langgraph", "lxml"]
    out: dict[str, str] = {}
    for name in pkgs:
        try:
            out[name] = md.version(name)
        except Exception:
            out[name] = ""
    return out


def _write_manifest(
    exp_dir: Path,
    *,
    cfg: Any,
    round_idx: int,
    seed: int | None,
    n_requirements: int,
    seeds: list[int],
    top_k: int,
    started_at: str,
    model_returned: str,
) -> None:
    import platform
    import sys as _sys

    bge_path = ""
    try:
        bge_path = str(cfg.model.embedding_model_path)
    except Exception:
        pass

    manifest = {
        "round": round_idx + 1,
        "seed": seed,
        "n_requirements": n_requirements,
        "groups": ["G1", "G2", "G3", "G4", "A1", "A2"],
        "model_alias_requested": cfg.deepseek.model,
        "model_returned": model_returned,
        "temperature": cfg.deepseek.temperature,
        "seeds": list(seeds),
        "top_k": top_k,
        "coarse_k": 12,
        "fine_k": 40,
        "rrf_k": 60,
        "coarse_bonus": 0.30,
        "group_expansion_base": 0.15,
        "started_at": started_at,
        "git_commit": "no-git",
        "python_version": _sys.version,
        "platform": platform.platform(),
        "bge_m3_model_path": bge_path,
        "package_versions": _gather_package_versions(),
        "llm_cache": cache_stats(),
    }
    (exp_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _run_one_round(
    round_idx: int,
    sampled_reqs: list[dict[str, Any]],
    cfg: Any,
    top_k: int,
    groups: set[str] | None = None,
    resume_dir: Path | None = None,
    seed: int | None = None,
    all_seeds: list[int] | None = None,
) -> tuple[Path, list[dict]]:
    """Run one complete round and return (exp_dir, metrics_rows).

    groups:     subset of ALL_GROUPS to execute; None means run all.
    resume_dir: existing exp_dir to add results into (partial re-run).
    """
    run_all = groups is None
    def _should_run(g: str) -> bool:
        return run_all or g in groups

    if resume_dir is not None:
        exp_dir = resume_dir
        exp_dir.mkdir(parents=True, exist_ok=True)
    else:
        batch_dir = make_batch_dir(cfg.paths.search_results_dir)
        exp_dir = batch_dir / "experiment"
        exp_dir.mkdir(parents=True, exist_ok=True)

    # Save the sampled requirements alongside results for traceability
    write_jsonl(str(exp_dir / "sampled_requirements.jsonl"), sampled_reqs)

    # ── Probe the LLM endpoint to capture the actual model returned, then
    # write the manifest BEFORE the run starts.  This guarantees we have a
    # record even if the run aborts mid-way.
    started_at = datetime.now().isoformat(timespec="seconds")
    model_returned = _probe_model(cfg)
    _write_manifest(
        exp_dir,
        cfg=cfg,
        round_idx=round_idx,
        seed=seed,
        n_requirements=len(sampled_reqs),
        seeds=all_seeds or [],
        top_k=top_k,
        started_at=started_at,
        model_returned=model_returned,
    )

    print(f"\n{'='*60}")
    print(f"ROUND {round_idx + 1} — {len(sampled_reqs)} requirements -> {exp_dir}")
    print(f"  model_returned={model_returned!r}  temperature={cfg.deepseek.temperature}")
    if not run_all:
        print(f"  (running groups: {sorted(groups)})")
    print(f"{'='*60}")

    g4_results = None

    # Load GPU model ONCE for the entire round; all groups share it
    needs_gpu = any(_should_run(g) for g in ["G2", "G3", "G4", "A2"])
    services = make_services() if needs_gpu else None
    if services:
        print(f"[Round {round_idx+1}] Shared model loaded on {services.retriever.evidence_searcher.model.device}")

    # G1
    if _should_run("G1"):
        print("\n--- G1: Direct LLM ---")
        g1_results = _run_g1_local(sampled_reqs, exp_dir, cfg)
        _save_group(g1_results, exp_dir, "G1")

    # G2
    if _should_run("G2"):
        print("\n--- G2: Flat RAG ---")
        g2_results = _run_g2_local(sampled_reqs, exp_dir, cfg, top_k, services=services)
        _save_group(g2_results, exp_dir, "G2")

    # G3
    if _should_run("G3"):
        print("\n--- G3: Multi-granular RAG (no QG) ---")
        g3_results = _run_pipeline_group_local(
            "G3", sampled_reqs, exp_dir, cfg,
            with_quality_gate=False, with_profile_scoring=True, top_k=top_k,
            services=services,
        )
        _save_group(g3_results, exp_dir, "G3")

    # G4
    if _should_run("G4"):
        print("\n--- G4: Proposed (multi-RAG + QG + SysML) ---")
        g4_results = _run_pipeline_group_local(
            "G4", sampled_reqs, exp_dir, cfg,
            with_quality_gate=True, with_profile_scoring=True, top_k=top_k,
            services=services,
        )
        _save_group(g4_results, exp_dir, "G4")

        # M6 人工审核文件（G4 保存后立即生成）
        print("\n--- M6: Generating human review file ---")
        _generate_m6_review(exp_dir, sampled_reqs, cfg)

    # A1 — derived from G4 (requires G4 to have run in this session)
    if _should_run("A1"):
        if g4_results is None:
            print("\n--- A1: skipped (G4 not run in this session) ---")
        else:
            print("\n--- A1: Ablation — no quality gate (derived from G4) ---")
            a1_results = copy.deepcopy(g4_results)
            for rs in a1_results:
                rs["_group"] = "A1"
                rs.pop("_quality_gate_summary", None)
                for er in rs.get("engineering_requirements") or []:
                    er.pop("quality_gate_report", None)
            _save_group(a1_results, exp_dir, "A1")
            print(f"  [A1] derived from G4: {len(a1_results)} sets")

    # A2
    if _should_run("A2"):
        print("\n--- A2: Ablation — no profile scoring ---")
        a2_results = _run_pipeline_group_local(
            "A2", sampled_reqs, exp_dir, cfg,
            with_quality_gate=True, with_profile_scoring=False, top_k=top_k,
            services=services,
        )
        _save_group(a2_results, exp_dir, "A2")

    # Release GPU after the whole round
    if services:
        del services
        _free_gpu()

    # 计算本轮指标（基于 exp_dir 中现有的所有组文件）
    present_groups = [g for g in ALL_GROUPS if (exp_dir / f"{g}_results.json").exists()]
    qg = QualityGate()
    metrics = _compute_metrics(exp_dir, present_groups, qg)
    (exp_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # manifest was written at round start (with model probe + full config).
    # Re-read and append final cache stats + finished_at + fallback summary so
    # reviewers can audit whether any LLM failures degraded results.
    try:
        manifest_path = exp_dir / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
            manifest["llm_cache_after"] = cache_stats()
            manifest["fallback_summary"] = _count_fallbacks(exp_dir, present_groups)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    except Exception as exc:
        print(f"[manifest] failed to update finished_at: {exc}")

    return exp_dir, metrics


def _count_fallbacks(exp_dir: Path, groups: list[str]) -> dict[str, dict[str, int]]:
    """Count LLM fallback events per group from saved result files.

    Two fallback types are tracked:
    - evidence_judge_fallback: sub-requirements where the evidence judge fell back
      to rule-based scoring (judge_method="fallback" in _judge_methods).
    - agent_fallback: requirement sets where the generation agent fell back
      (generation_mode="fallback" in the result set).
    """
    summary: dict[str, dict[str, int]] = {}
    for group in groups:
        path = exp_dir / f"{group}_results.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        result_sets = data.get("result_sets", [])
        ej_fallback = sum(
            1
            for rs in result_sets
            for jm in (rs.get("_judge_methods") or [])
            if jm.get("judge_method") == "fallback"
        )
        agent_fallback = sum(
            1 for rs in result_sets
            if rs.get("generation_mode") == "fallback"
        )
        summary[group] = {
            "evidence_judge_fallback": ej_fallback,
            "agent_fallback": agent_fallback,
            "total_result_sets": len(result_sets),
        }
    return summary


def _save_group(results: list[dict], exp_dir: Path, group: str) -> None:
    (exp_dir / f"{group}_results.json").write_text(
        json.dumps({"group": group, "result_sets": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _generate_m6_review(
    exp_dir: Path,
    sampled_reqs: list[dict],
    cfg: Any,
) -> None:
    """G4 保存后自动生成供人工审核的 M6_review.json。已存在则跳过以保护审核进度。"""
    out_path = exp_dir / "M6_review.json"
    if out_path.exists():
        print(f"  [M6] review file already exists, skipping -> {out_path.name}")
        return

    g4_path = exp_dir / "G4_results.json"
    if not g4_path.exists():
        print("  [M6] G4_results.json not found, skipping M6 generation")
        return

    # 证据文本查找表
    ev_lookup: dict[str, dict] = {}
    ev_path = Path(cfg.paths.evidence_units_jsonl)
    if ev_path.exists():
        with ev_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ev_id = obj.get("id", "")
                    if ev_id:
                        meta = obj.get("metadata") or {}
                        ev_lookup[ev_id] = {
                            "text": obj.get("text", ""),
                            "source_file": str(meta.get("source_document", "") or ""),
                        }
                except json.JSONDecodeError:
                    continue

    # 原始需求查找表
    req_lookup = {
        r["requirement_id"]: {
            "stakeholder": r.get("stakeholder", ""),
            "text": r.get("requirement_text", ""),
        }
        for r in sampled_reqs
    }

    raw = json.loads(g4_path.read_text(encoding="utf-8"))
    result_sets: list[dict] = raw["result_sets"] if isinstance(raw, dict) else raw

    rs_list = []
    for rs in result_sets:
        src_id = rs.get("source_requirement_id", "")
        src_info = req_lookup.get(src_id, {})
        er_list = []
        for er in (rs.get("engineering_requirements") or []):
            ev_items = []
            for ev_id in (er.get("evidence_ids") or []):
                ev = ev_lookup.get(ev_id, {})
                ev_items.append({
                    "ev_id": ev_id,
                    "source_file": ev.get("source_file", ""),
                    "text": ev.get("text", ""),
                })
            er_list.append({
                "er_id": er.get("id", ""),
                "requirement_type": er.get("requirement_type", ""),
                "shall_statement": er.get("shall_statement", ""),
                "verification_method": er.get("verification_method", ""),
                "support_status": er.get("support_status", ""),
                "acceptance_criteria": er.get("acceptance_criteria") or [],
                "evidence": ev_items,
                "review": {
                    "decomposition_correct": None,
                    "traceability_correct": None,
                    "notes": "",
                },
            })
        rs_list.append({
            "source_requirement_id": src_id,
            "stakeholder": src_info.get("stakeholder") or rs.get("stakeholder", ""),
            "source_text": src_info.get("text", ""),
            "engineering_requirements": er_list,
        })

    total_ers = sum(len(r["engineering_requirements"]) for r in rs_list)
    review = {
        "_instructions": {
            "decomposition_correct": "拆分合理性：true（这条 shall 是原始需求的合理拆分）/ false（拆分不合理）/ null（未审核）",
            "traceability_correct": "证据支撑性：true（证据支持该 shall）/ false（不支持/无关）/ null（未审核，或该 ER 无证据时保持 null）",
            "notes": "可填写任意审核备注，也可留空",
            "直接编辑说明": "本文件可直接用文本编辑器修改并保存，m6_review_ui 打开时会自动读取",
        },
        "batch": exp_dir.parent.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "last_saved_at": None,
        "total_ers": total_ers,
        "reviewed_count": 0,
        "requirement_sets": rs_list,
    }
    out_path.write_text(
        json.dumps(review, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  [M6] Generated -> {out_path.name}  ({total_ers} ERs, {len(rs_list)} requirement sets)")


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--seeds", nargs=3, type=int, default=[42, 7, 99],
                        help="Random seeds for the 3 rounds (default: 42 7 99)")
    parser.add_argument("--sample-n", type=int, default=30,
                        help="Requirements to sample per round (default: 30)")
    parser.add_argument("--start-round", type=int, default=1, metavar="N",
                        help="Start from round N (1-indexed). Skip earlier rounds.")
    parser.add_argument("--groups", nargs="+", choices=ALL_GROUPS, metavar="GROUP",
                        help="Run only these groups (e.g. --groups A2). Default: all.")
    parser.add_argument("--resume-batch", metavar="BATCH_DIR",
                        help="Existing batch dir name (e.g. batch_20260526_164635) to resume "
                             "into for the first active round. Useful with --groups.")
    args = parser.parse_args()

    cfg = get_config()
    pool_path = cfg.paths.processed_dir / "requirement_pool_100.jsonl"

    if not pool_path.exists():
        print(f"Requirement pool not found: {pool_path}")
        print("Run: python scripts/25_generate_requirement_pool.py")
        sys.exit(1)

    pool = read_jsonl(str(pool_path))
    print(f"Loaded pool: {len(pool)} requirements")
    if len(pool) < args.sample_n:
        print(f"Pool has only {len(pool)} requirements, sampling all.")
        args.sample_n = len(pool)

    groups_set = set(args.groups) if args.groups else None
    start_idx = args.start_round - 1  # convert to 0-indexed

    # Resolve --resume-batch to an absolute exp_dir path
    resume_exp_dir: Path | None = None
    if args.resume_batch:
        candidate = cfg.paths.search_results_dir / args.resume_batch / "experiment"
        if not candidate.exists():
            print(f"resume-batch dir not found: {candidate}")
            sys.exit(1)
        resume_exp_dir = candidate
        print(f"Resuming into: {resume_exp_dir}")

    all_round_metrics: list[list[dict]] = []
    round_batch_dirs: list[str] = []

    for i, seed in enumerate(args.seeds):
        if i < start_idx:
            print(f"\nRound {i+1}: skipped (--start-round {args.start_round})")
            continue

        random.seed(seed)
        seed_everything(seed)
        sampled = random.sample(pool, args.sample_n)
        print(f"\nRound {i+1} seed={seed}: sampled {len(sampled)} requirements")
        stakeholders = {}
        for r in sampled:
            s = r.get("stakeholder", "?")
            stakeholders[s] = stakeholders.get(s, 0) + 1
        print("  Stakeholders:", dict(sorted(stakeholders.items())))

        # Use resume_exp_dir only for the first active round
        use_resume = resume_exp_dir if (i == start_idx and resume_exp_dir) else None
        exp_dir, metrics = _run_one_round(i, sampled, cfg, args.top_k,
                                          groups=groups_set, resume_dir=use_resume,
                                          seed=seed, all_seeds=args.seeds)
        all_round_metrics.append(metrics)
        round_batch_dirs.append(str(exp_dir))
        print(f"\nRound {i+1} complete -> {exp_dir}")

    # Aggregate across rounds
    summary = _aggregate(all_round_metrics)
    _print_summary(summary)

    out_path = cfg.paths.search_results_dir / "three_round_summary.json"
    out_path.write_text(
        json.dumps({
            "seeds": args.seeds,
            "sample_n": args.sample_n,
            "top_k": args.top_k,
            "round_dirs": round_batch_dirs,
            "summary": summary,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSummary saved -> {out_path}")
    print("\nNext: python scripts/22_compute_metrics.py --exp-dir <any round dir>")


if __name__ == "__main__":
    main()
