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

from cooling_rag_mg.config import get_config
from cooling_rag_mg.engineering_requirement_agent import (
    generate_engineering_requirements,
)
from cooling_rag_mg.evidence_pack import make_batch_dir
from cooling_rag_mg.jsonl import read_jsonl, write_jsonl
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
# G1: Direct LLM（无检索）
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


def _run_g1(
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
) -> list[dict[str, Any]]:
    from openai import OpenAI
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
    results = []
    for r in reqs:
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
            print(f"  [G1] {r['requirement_id']} ✓")
        except Exception as exc:
            print(f"  [G1] {r['requirement_id']} ✗ {exc}")

    write_jsonl(str(exp_dir / "G1_direct_llm.jsonl"), results)
    return results


# ─────────────────────────────────────────────
# G2: Flat RAG（单粒度检索，不使用 run_requirements_with_services）
# ─────────────────────────────────────────────

def _build_flat_retrieval_payload(
    reqs: list[dict[str, Any]],
    cfg: Any,
    top_k: int,
) -> dict[str, Any]:
    """
    Build a retrieval_payload compatible with generate_engineering_requirements
    using flat (single-granularity) evidence_units retrieval.
    """
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

        # Wrap as selected_results (all marked as "indirect" since no LLM judge)
        selected = []
        for c in candidates:
            c = dict(c)
            c["llm_judge"] = {"support_type": "indirect", "evidence_role": "supporting"}
            selected.append(c)

        # Build one synthetic sub-requirement containing all flat results
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


def _run_g2(
    reqs: list[dict[str, Any]],
    exp_dir: Path,
    cfg: Any,
    top_k: int,
) -> list[dict[str, Any]]:
    pipeline_reqs = _to_pipeline_input(reqs)
    retrieval_payload = _build_flat_retrieval_payload(reqs, cfg, top_k)
    output = generate_engineering_requirements(pipeline_reqs, retrieval_payload)
    results = []
    for rs in output.get("requirement_sets", []):
        rs["_group"] = "G2"
        results.append(rs)
        print(f"  [G2] {rs.get('source_requirement_id')} ✓")

    write_jsonl(str(exp_dir / "G2_flat_rag.jsonl"), results)
    return results


# ─────────────────────────────────────────────
# G3 / G4 / A1 / A2: 使用正确的 pipeline 接口
# ─────────────────────────────────────────────

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

    if with_quality_gate:
        results = _attach_quality_gate(results)

    if group == "G4":
        xml_dir = exp_dir / "G4_sysml_xml"
        export_batch(results, xml_dir)
        print(f"  [G4] SysML XML → {xml_dir}")

    write_jsonl(str(exp_dir / f"{group}_results.jsonl"), results)
    return results


def _disable_profile_scoring(retriever: Any) -> None:
    """A2 ablation: bypass profile scoring, sort by rrf_score only."""
    def _flat(items: list[dict], profile: dict, *, is_chunk: bool = False) -> list[dict]:
        for item in items:
            item["profile_score"] = 0.0
            item["final_score"] = float(item.get("rrf_score", 0.0))
        return items
    retriever._score_by_profile = _flat  # type: ignore[method-assign]


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
        _run_pipeline_group(
            "G4", reqs, exp_dir, cfg,
            with_quality_gate=True, with_profile_scoring=True, top_k=top_k,
        )

    if "A1" in groups:
        print("\n=== A1: Ablation — no quality gate ===")
        _run_pipeline_group(
            "A1", reqs, exp_dir, cfg,
            with_quality_gate=False, with_profile_scoring=True, top_k=top_k,
        )

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
