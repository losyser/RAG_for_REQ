# -*- coding: utf-8 -*-
"""
Experiment runner — in-memory versions of scripts/21 and scripts/22.
All functions return Python objects; no file I/O.
"""
from __future__ import annotations

import json
import math
from typing import Any, Callable

from cooling_rag_mg.quality_gate import QualityGate
from cooling_rag_mg.text_utils import safe_text

# ─────────────────────────────────────────────
# G1 system prompt
# ─────────────────────────────────────────────

_G1_SYSTEM = """\
You are a marine main engine cooling water system requirements engineer.

Task: Transform the stakeholder's raw requirement into structured engineering requirements
based solely on your domain knowledge (no retrieval evidence is available).

Rules:
- Write shall_statement in clear engineering language
- Set evidence_ids to empty list
- Set support_status to "no_evidence_baseline"
- For parameter values you cannot confirm, use placeholder:
  "to be confirmed per Manufacturer Technical Data"
- Do NOT fabricate specific numerical values
- verification_method MUST be one of: review, inspection, calculation, test,
  commissioning_check, operation_check, maintenance_check, class_approval
- requirement_type MUST be one of: reliability, redundancy, parameter, control,
  alarm_protection, configuration, verification, installation, maintainability,
  operation, safety_environment, other

Output valid JSON only (no markdown):
{
  "requirement_set_id": "ER-G1-<id>",
  "source_requirement_id": "<id>",
  "stakeholder": "<stakeholder>",
  "generation_basis": "direct_llm_no_evidence",
  "professional_summary": "...",
  "assumptions": [],
  "engineering_requirements": [
    {
      "id": "ER-G1-<id>-01",
      "parent_id": "ER-G1-<id>",
      "level": 1,
      "requirement_type": "other",
      "topic": "...",
      "shall_statement": "...",
      "engineering_rationale": "Generated from domain knowledge without evidence.",
      "acceptance_criteria": ["..."],
      "verification_method": "review",
      "evidence_ids": [],
      "support_status": "no_evidence_baseline",
      "applicability_constraints": [],
      "risk_if_unmet": "..."
    }
  ],
  "relationships": [],
  "evidence_gaps": [],
  "confirmation_items": []
}
"""

# ─────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────

def to_pipeline_input(reqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": r["requirement_id"],
            "stakeholder": r.get("stakeholder", ""),
            "requirement_text": r.get("requirement_text", ""),
        }
        for r in reqs
    ]


ProgressCallback = Callable[[int, int, str], None]


# ─────────────────────────────────────────────
# G1: Direct LLM
# ─────────────────────────────────────────────

def run_g1(
    reqs: list[dict[str, Any]],
    cfg: Any,
    on_progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    from openai import OpenAI
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
    results = []
    for i, r in enumerate(reqs):
        if on_progress:
            on_progress(i, len(reqs), r["requirement_id"])
        try:
            payload = {
                "requirement_id": r["requirement_id"],
                "stakeholder": r.get("stakeholder", ""),
                "raw_requirement": r.get("requirement_text", ""),
            }
            resp = client.chat.completions.create(
                model=cfg.deepseek.model,
                messages=[
                    {"role": "system", "content": _G1_SYSTEM},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=0.1,
                max_tokens=cfg.deepseek.max_tokens_requirement_agent,
                response_format={"type": "json_object"},
            )
            obj = json.loads(resp.choices[0].message.content or "{}")
            obj["_group"] = "G1"
            results.append(obj)
        except Exception as exc:
            results.append({
                "_group": "G1",
                "source_requirement_id": r["requirement_id"],
                "_error": str(exc),
                "engineering_requirements": [],
            })
    if on_progress:
        on_progress(len(reqs), len(reqs), "done")
    return results


# ─────────────────────────────────────────────
# G2: Flat RAG
# ─────────────────────────────────────────────

def _build_flat_retrieval_payload(
    reqs: list[dict[str, Any]],
    cfg: Any,
    top_k: int,
) -> dict[str, Any]:
    from cooling_rag_mg.hybrid_fusion import rrf_fuse
    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index

    searcher = HybridIndexSearcher(
        load_index(str(cfg.paths.indexes_dir / "evidence_units")),
        device=cfg.model.device,
    )
    requirement_results = []
    for r in reqs:
        query = r.get("requirement_text", "")
        vec = searcher.vector_search(query, top_k * 4)
        bm25 = searcher.bm25_search(query, top_k * 4)
        candidates = rrf_fuse([vec, bm25])[:top_k]
        selected = []
        for c in candidates:
            c = dict(c)
            c["llm_judge"] = {"support_type": "indirect", "evidence_role": "supporting"}
            selected.append(c)
        synthetic_sub = {
            "sub_requirement_id": f"{r['requirement_id']}-01",
            "requirement_type": "other",
            "topic": r.get("requirement_text", "")[:40],
            "text": r.get("requirement_text", ""),
            "selected_results": selected,
            "evidence_gap": None,
        }
        requirement_results.append({
            "requirement_id": r["requirement_id"],
            "stakeholder": r.get("stakeholder", ""),
            "raw_requirement_text": r.get("requirement_text", ""),
            "sub_requirements": [synthetic_sub],
        })
    return {"requirements": requirement_results, "diagnostics": {}}


def run_g2(
    reqs: list[dict[str, Any]],
    cfg: Any,
    top_k: int = 4,
    on_progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    from cooling_rag_mg.engineering_requirement_agent import generate_engineering_requirements
    if on_progress:
        on_progress(0, len(reqs), "构建扁平检索载荷")
    retrieval_payload = _build_flat_retrieval_payload(reqs, cfg, top_k)
    if on_progress:
        on_progress(0, len(reqs), "调用工程需求智能体")
    pipeline_reqs = to_pipeline_input(reqs)
    output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
    results = []
    for rs in output.get("requirement_sets", []):
        rs["_group"] = "G2"
        results.append(rs)
    if on_progress:
        on_progress(len(reqs), len(reqs), "done")
    return results


# ─────────────────────────────────────────────
# G3 / G4 / A1 / A2
# ─────────────────────────────────────────────

def _disable_profile_scoring(retriever: Any) -> None:
    def _flat(items: list[dict], profile: dict, *, is_chunk: bool = False) -> list[dict]:
        for item in items:
            item["profile_score"] = 0.0
            item["final_score"] = float(item.get("rrf_score", 0.0))
        return items
    retriever._score_by_profile = _flat  # type: ignore[method-assign]


def attach_quality_gate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def run_pipeline_group(
    group: str,
    reqs: list[dict[str, Any]],
    cfg: Any,
    *,
    with_quality_gate: bool,
    with_profile_scoring: bool,
    top_k: int = 4,
    services: Any = None,
    on_progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    from cooling_rag_mg.engineering_requirement_agent import generate_engineering_requirements
    from cooling_rag_mg.pipeline import make_services, run_requirements_with_services

    pipeline_reqs = to_pipeline_input(reqs)
    if on_progress:
        on_progress(0, len(reqs), "初始化服务")
    if services is None:
        services = make_services()
    if not with_profile_scoring:
        _disable_profile_scoring(services.retriever)
    if on_progress:
        on_progress(0, len(reqs), "多粒度检索中")
    retrieval_payload = run_requirements_with_services(
        pipeline_reqs,
        services=services,
        top_k=top_k,
        coarse_k=12,
        fine_k=40,
    )
    if on_progress:
        on_progress(0, len(reqs), "工程需求生成中")
    output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
    results = []
    for rs in output.get("requirement_sets", []):
        rs["_group"] = group
        results.append(rs)
    if with_quality_gate:
        if on_progress:
            on_progress(0, len(reqs), "质量门检查中")
        results = attach_quality_gate(results)
    if on_progress:
        on_progress(len(reqs), len(reqs), "done")
    return results


# ─────────────────────────────────────────────
# Metrics (from scripts/22)
# ─────────────────────────────────────────────

def flatten_requirements(result_sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for rs in result_sets:
        for er in (rs.get("engineering_requirements") or []):
            er = dict(er)
            er["_group"] = rs.get("_group", "")
            er["_set_id"] = rs.get("requirement_set_id", "")
            out.append(er)
    return out


def compute_metrics(results_by_group: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """
    results_by_group: {"G1": [result_set, ...], "G4": [...], ...}
    Returns list of metric dicts ordered by group insertion order.
    """
    qg = QualityGate()
    rows = []
    for group, result_sets in results_by_group.items():
        if not result_sets:
            continue
        reqs = flatten_requirements(result_sets)

        def _nan_safe(n: int, d: int) -> float:
            return round(n / d, 4) if d else float("nan")

        # M1
        empty_ev = sum(1 for r in reqs if not (r.get("evidence_ids") or []))
        m1 = _nan_safe(empty_ev, len(reqs))

        # M2
        has_report = [r for r in reqs if r.get("quality_gate_report")]
        if has_report:
            passed_qg = sum(1 for r in has_report if (r.get("quality_gate_report") or {}).get("overall_passed"))
            m2 = _nan_safe(passed_qg, len(has_report))
        else:
            m2 = float("nan")

        # M3
        failed_oi = sum(1 for r in reqs if not qg._over_inference(r).passed)  # noqa: SLF001
        m3 = _nan_safe(failed_oi, len(reqs))

        # M4
        passed_ver = sum(1 for r in reqs if qg._verifiability(r).passed)  # noqa: SLF001
        m4 = _nan_safe(passed_ver, len(reqs))

        # M5
        passed_mbse = sum(1 for r in reqs if qg._mbse_completeness(r).passed)  # noqa: SLF001
        m5 = _nan_safe(passed_mbse, len(reqs))

        rows.append({
            "group": group,
            "n_sets": len(result_sets),
            "n_reqs": len(reqs),
            "m1": m1, "m2": m2, "m3": m3, "m4": m4, "m5": m5,
        })
    return rows


# ─────────────────────────────────────────────
# M6 template generation
# ─────────────────────────────────────────────

def generate_m6_template(result_sets: list[dict[str, Any]], n: int = 20) -> list[dict[str, Any]]:
    reqs = flatten_requirements(result_sets)
    sample = reqs[:n]
    out = []
    for i, r in enumerate(sample, start=1):
        out.append({
            "index": i,
            "requirement_id": safe_text(r.get("id")),
            "shall_statement": safe_text(r.get("shall_statement")),
            "evidence_ids": r.get("evidence_ids") or [],
            "support_status": safe_text(r.get("support_status")),
            "source_set_id": r.get("_set_id", ""),
            "M6_human_judgement": {
                "traceability_correct": None,
                "notes": "",
            },
        })
    return out
