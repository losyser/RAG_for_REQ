# -*- coding: utf-8 -*-
"""
Script 21: Run 4-group comparison experiment + 2 ablation groups.

Groups:
  G1  Direct LLM        — no retrieval, custom unconstrained prompt
  G2  Flat RAG          — single-granularity (evidence_units only), no quality gate
  G3  Multi-RAG         — multi-granular retrieval, no quality gate
  G4  Proposed          — multi-granular retrieval + quality gate + SysML XML

Ablation:
  A1  G4 - QualityGate  — multi-granular, quality gate disabled
  A2  G4 - Profile      — multi-granular, profile scoring disabled (flat RRF only)

Correct call pattern (for G3/G4/A1/A2):
  retrieval_payload = run_requirements_with_services(reqs, services=services)
  output = generate_engineering_requirements(reqs, retrieval_payload)

Usage:
  python scripts/21_run_experiment.py [--groups G1 G2 G3 G4 A1 A2] [--top-k 4]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import copy

from cooling_rag_mg.config import get_config
from cooling_rag_mg.engineering_requirement_agent import (
    ENGINEERING_REQUIREMENT_PROMPT,
    generate_engineering_requirements,
)
from cooling_rag_mg.evidence_pack import make_batch_dir
from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
from cooling_rag_mg.llm_cache import cached_completion
from cooling_rag_mg.pipeline import make_services, run_requirements_with_services
from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.sysml_exporter import export_batch

ALL_GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]


# ─────────────────────────────────────────────
# 辅助：把 test_requirements.jsonl 的条目标准化为 pipeline 输入格式
# ─────────────────────────────────────────────

def _to_pipeline_input(reqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": r["requirement_id"],
            "stakeholder": r.get("stakeholder", ""),
            "requirement_text": r.get("requirement_text", ""),
        }
        for r in reqs
    ]


# ─────────────────────────────────────────────
# G1: Paired baseline — same prompt as G2-G4, empty retrieval context
# ─────────────────────────────────────────────

_G1_USER_MARKER = (
    "This is a no-evidence baseline; produce shall statements based on the "
    "requirement text alone. Do not fabricate evidence_ids — leave evidence_ids "
    "empty for every engineering requirement. Set support_status to "
    "'no_evidence_baseline'. Do not invent specific quantitative values; use "
    "the standard placeholders defined in the prompt (e.g., '按主机厂家 "
    "Technical Data 确认')."
)


def _run_g1(
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
) -> list[dict[str, Any]]:
    """G1 paired baseline — identical system prompt to G2-G4 with empty evidence."""
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

    write_jsonl(str(exp_dir / "G1_direct_llm.jsonl"), results)
    return results


# ─────────────────────────────────────────────
# G2: Flat RAG（单粒度检索，不使用 run_requirements_with_services）
# ─────────────────────────────────────────────

def _build_flat_retrieval_payload(
    reqs: list[dict[str, Any]],
    cfg: Any,
    top_k: int,
    services: Any,
) -> dict[str, Any]:
    """Single-granularity retrieval (evidence_units only, flat RRF).

    Uses the same applicability_filter and evidence_judge as G3/G4 so that
    G2 vs G3 isolates retrieval granularity only.
    """
    from cooling_rag_mg.evidence_judge import apply_judge
    from cooling_rag_mg.hybrid_fusion import rrf_fuse
    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index

    searcher = HybridIndexSearcher(
        load_index(str(cfg.paths.indexes_dir / "evidence_units")),
        device=cfg.model.device,
    )
    requirement_results = []
    for r in reqs:
        query = r.get("requirement_text", "")
        vec = searcher.vector_search(query, top_k * 6)
        bm25 = searcher.bm25_search(query, top_k * 6)
        candidates = rrf_fuse([vec, bm25])

        synthetic_sub = {
            "sub_requirement_id": f"{r['requirement_id']}-01",
            "requirement_type": "other",
            "topic": r.get("requirement_text", "")[:40],
            "text": r.get("requirement_text", ""),
        }

        # Same filter + judge pipeline as G3/G4
        applicable, _ = services.applicability_filter.apply(
            synthetic_sub, candidates, top_k_for_judge=top_k * 3,
        )
        judge_result = services.judge(synthetic_sub, applicable, max_selected=top_k)
        selected, _ = apply_judge(applicable, judge_result)

        requirement_results.append({
            "requirement_id": r["requirement_id"],
            "stakeholder": r.get("stakeholder", ""),
            "raw_requirement_text": r.get("requirement_text", ""),
            "sub_requirements": [{
                **synthetic_sub,
                "selected_results": selected,
                "evidence_gap": None,
            }],
        })
    return {"requirements": requirement_results, "diagnostics": {}}


def _run_g2(
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
    top_k: int,
) -> list[dict[str, Any]]:
    services = make_services()
    pipeline_reqs = _to_pipeline_input(reqs)
    retrieval_payload = _build_flat_retrieval_payload(reqs, cfg, top_k, services)
    output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
    results = []
    for rs in output.get("requirement_sets", []):
        rs["_group"] = "G2"
        results.append(rs)
        print(f"  [G2] {rs.get('source_requirement_id')} ✓")

    results = _attach_judge_methods(results, retrieval_payload)
    write_jsonl(str(exp_dir / "G2_flat_rag.jsonl"), results)
    return results


# ─────────────────────────────────────────────
# G3 / G4 / A1 / A2: 使用正确的 pipeline 接口
# ─────────────────────────────────────────────

def _attach_judge_methods(
    results: list[dict[str, Any]],
    retrieval_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve stage_diagnostics.judge_method into saved results per sub_requirement."""
    from cooling_rag_mg.text_utils import safe_text
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


def _attach_quality_gate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def _run_pipeline_group(
    group: str,
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
    *,
    with_quality_gate: bool,
    with_profile_scoring: bool,
    top_k: int,
) -> list[dict[str, Any]]:
    pipeline_reqs = _to_pipeline_input(reqs)
    services = make_services()

    if not with_profile_scoring:
        _disable_profile_scoring(services.retriever)

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
        print(f"  [{group}] {rs.get('source_requirement_id')} ✓")

    results = _attach_judge_methods(results, retrieval_payload)

    if with_quality_gate:
        results = _attach_quality_gate(results)

    if group == "G4":
        xml_dir = exp_dir / "G4_sysml_xml"
        export_batch(results, xml_dir)
        print(f"  [G4] SysML XML → {xml_dir}")

    write_jsonl(str(exp_dir / f"{group}_results.jsonl"), results)
    return results


def _disable_profile_scoring(retriever: Any) -> None:
    """A2 ablation: bypass all profile-based scoring and filtering.

    Replaces both _score_by_profile and _soft_filter_by_profile so A2
    reflects pure RRF with no profile influence.  Data-quality hard-rejects
    (not_applicable, is_noise) are preserved.
    """
    def _flat_score(items: list[dict], profile: dict, *, is_chunk: bool = False) -> list[dict]:
        for item in items:
            item["profile_score"] = 0.0
            item["final_score"] = float(item.get("rrf_score", 0.0))
        return items

    def _flat_filter(items: list[dict], profile: dict) -> list[dict]:
        from cooling_rag_mg.schema import normalize_v2_metadata
        from cooling_rag_mg.text_utils import safe_text as _st
        out = []
        for item in items:
            meta = normalize_v2_metadata(item.get("metadata", {}) or {})
            if _st(meta.get("evidence_strength")).lower() == "not_applicable":
                continue
            if meta.get("is_noise") is True:
                continue
            item["retrieval_role"] = item.get("retrieval_role") or "candidate"
            item["metadata"] = meta
            out.append(item)
        return out

    retriever._score_by_profile = _flat_score  # type: ignore[method-assign]
    retriever._soft_filter_by_profile = _flat_filter  # type: ignore[method-assign]


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--groups", nargs="+", default=ALL_GROUPS, choices=ALL_GROUPS,
    )
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    cfg = get_config()
    test_req_path = cfg.paths.processed_dir / "test_requirements.jsonl"

    if not test_req_path.exists():
        print(f"Test requirements not found: {test_req_path}")
        print("Run: python scripts/20_generate_test_requirements.py")
        sys.exit(1)

    reqs = read_jsonl(str(test_req_path))
    print(f"Loaded {len(reqs)} test requirements\n")

    batch_dir = make_batch_dir(cfg.paths.search_results_dir)
    exp_dir = batch_dir / "experiment"
    exp_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {exp_dir}\n")

    groups = args.groups
    top_k = args.top_k
    g4_results = None  # shared across G4 and A1

    if "G1" in groups:
        print("=== G1: Direct LLM ===")
        _run_g1(reqs, exp_dir, cfg)

    if "G2" in groups:
        print("\n=== G2: Flat RAG ===")
        _run_g2(reqs, exp_dir, cfg, top_k)

    if "G3" in groups:
        print("\n=== G3: Multi-granular RAG (no QG) ===")
        _run_pipeline_group(
            "G3", reqs, exp_dir, cfg,
            with_quality_gate=False, with_profile_scoring=True, top_k=top_k,
        )

    if "G4" in groups:
        print("\n=== G4: Proposed (multi-RAG + QG + SysML) ===")
        g4_results = _run_pipeline_group(
            "G4", reqs, exp_dir, cfg,
            with_quality_gate=True, with_profile_scoring=True, top_k=top_k,
        )

    if "A1" in groups:
        print("\n=== A1: Ablation — no quality gate (derived from G4) ===")
        if g4_results is None:
            # G4 wasn't selected — must run it now to share retrieval + generation
            print("  [A1] G4 not in selected groups; running G4 first to share results...")
            g4_results = _run_pipeline_group(
                "G4", reqs, exp_dir, cfg,
                with_quality_gate=True, with_profile_scoring=True, top_k=top_k,
            )
        a1_results = copy.deepcopy(g4_results)
        for rs in a1_results:
            rs["_group"] = "A1"
            rs.pop("_quality_gate_summary", None)
            for er in rs.get("engineering_requirements") or []:
                er.pop("quality_gate_report", None)
        write_jsonl(str(exp_dir / "A1_results.jsonl"), a1_results)
        print(f"  [A1] derived from G4: {len(a1_results)} sets")

    if "A2" in groups:
        print("\n=== A2: Ablation — no profile scoring ===")
        _run_pipeline_group(
            "A2", reqs, exp_dir, cfg,
            with_quality_gate=True, with_profile_scoring=False, top_k=top_k,
        )

    print(f"\nDone. Results in: {exp_dir}")
    print("Next: python scripts/22_compute_metrics.py")


if __name__ == "__main__":
    main()
