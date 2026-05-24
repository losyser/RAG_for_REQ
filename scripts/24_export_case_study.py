# -*- coding: utf-8 -*-
"""
Script 24: Export one G4 requirement set as a paper-ready case study.

Outputs:
  - case_study_<set_id>.md   — human-readable overview for the paper
  - case_study_<set_id>.json — full structured data

Usage:
    python scripts/24_export_case_study.py [--exp-dir <path>] [--index 0]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.text_utils import safe_text


def _fmt_er(er: dict) -> str:
    lines = []
    eid = safe_text(er.get("id"))
    level = er.get("level", 1)
    indent = "  " * (level - 1)
    lines.append(f"{indent}### {eid}  ({er.get('requirement_type', 'other')})")
    lines.append(f"{indent}**Shall:** {safe_text(er.get('shall_statement'))}")
    lines.append(f"{indent}**Status:** `{safe_text(er.get('support_status'))}`  "
                 f"**Method:** `{safe_text(er.get('verification_method'))}`")
    ev_ids = er.get("evidence_ids") or []
    if ev_ids:
        lines.append(f"{indent}**Evidence:** {', '.join(ev_ids)}")
    criteria = er.get("acceptance_criteria") or []
    if criteria:
        lines.append(f"{indent}**Acceptance criteria:**")
        for c in criteria:
            lines.append(f"{indent}- {c}")
    qg = er.get("quality_gate_report")
    if qg:
        passed = "PASS" if qg.get("overall_passed") else "FAIL"
        score = qg.get("score", 0)
        lines.append(f"{indent}**Quality gate:** {passed} (score={score:.2f})")
        for chk in (qg.get("checks") or []):
            sym = "✓" if chk.get("passed") else "✗"
            lines.append(f"{indent}  {sym} `{chk['dimension']}` — {chk['message']}")
    lines.append("")
    return "\n".join(lines)


def generate_case_study_md(rs: dict) -> str:
    lines = [
        f"# Case Study: {safe_text(rs.get('requirement_set_id'))}",
        "",
        f"**Source requirement:** `{safe_text(rs.get('source_requirement_id'))}`  ",
        f"**Stakeholder:** {safe_text(rs.get('stakeholder'))}  ",
        f"**Group:** {rs.get('_group', 'G4')}",
        "",
        "## Professional Summary",
        "",
        safe_text(rs.get("professional_summary")),
        "",
    ]

    assumptions = rs.get("assumptions") or []
    if assumptions:
        lines += ["## Assumptions", ""]
        for a in assumptions:
            lines.append(f"- {a}")
        lines.append("")

    lines += ["## Engineering Requirements", ""]
    all_reqs = rs.get("engineering_requirements") or []
    top_level = [r for r in all_reqs if r.get("level", 1) == 1]
    for req in top_level:
        lines.append(_fmt_er(req))
        children = [r for r in all_reqs
                    if safe_text(r.get("parent_id")) == safe_text(req.get("id"))
                    and r.get("level", 1) == 2]
        for child in children:
            lines.append(_fmt_er(child))

    gaps = rs.get("evidence_gaps") or []
    if gaps:
        lines += ["## Evidence Gaps", ""]
        for g in gaps:
            lines.append(f"- **{safe_text(g.get('gap_type'))}** "
                         f"({safe_text(g.get('related_requirement_id'))}): "
                         f"{safe_text(g.get('description'))}")
            if g.get("suggested_document_update"):
                lines.append(f"  → {safe_text(g.get('suggested_document_update'))}")
        lines.append("")

    conf = rs.get("confirmation_items") or []
    if conf:
        lines += ["## Confirmation Items", ""]
        for item in conf:
            lines.append(f"- {safe_text(item.get('item'))}")
            if item.get("reason"):
                lines.append(f"  *(Reason: {safe_text(item.get('reason'))})*")
        lines.append("")

    qg_summary = rs.get("_quality_gate_summary")
    if qg_summary:
        lines += ["## Quality Gate Summary", ""]
        lines.append(
            f"- Total requirements: {qg_summary.get('total', 0)}"
        )
        lines.append(
            f"- Passed: {qg_summary.get('passed', 0)} / {qg_summary.get('total', 0)}"
        )
        lines.append(
            f"- Average score: {qg_summary.get('avg_score', 0):.2f}"
        )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", default=None)
    parser.add_argument("--index", type=int, default=0,
                        help="Index of the requirement set in G4 results (0-based)")
    parser.add_argument("--group", default="G4",
                        help="Which group to pick the case study from (default: G4)")
    args = parser.parse_args()

    cfg = get_config()
    if args.exp_dir:
        exp_dir = Path(args.exp_dir)
    else:
        batches = sorted(cfg.paths.search_results_dir.glob("batch_*/experiment"))
        if not batches:
            print("No experiment directory found. Run scripts 21 and 22 first.")
            sys.exit(1)
        exp_dir = batches[-1]

    group = args.group
    candidates = list(exp_dir.glob(f"{group}_*.jsonl"))
    if not candidates:
        print(f"No {group} results found in {exp_dir}")
        sys.exit(1)

    result_sets = read_jsonl(str(candidates[0]))
    if not result_sets:
        print(f"{group} results file is empty.")
        sys.exit(1)

    idx = min(args.index, len(result_sets) - 1)
    rs = result_sets[idx]
    set_id = safe_text(rs.get("requirement_set_id")) or f"{group}-{idx}"

    md = generate_case_study_md(rs)
    md_path = exp_dir / f"case_study_{set_id}.md"
    json_path = exp_dir / f"case_study_{set_id}.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(rs, ensure_ascii=False, indent=2), encoding="utf-8")

    print(md)
    print(f"\nCase study → {md_path}")
    print(f"Full JSON  → {json_path}")


if __name__ == "__main__":
    main()
