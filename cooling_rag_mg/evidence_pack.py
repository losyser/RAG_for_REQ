from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from cooling_rag_mg.text_utils import safe_text


def make_batch_dir(root: str | Path) -> Path:
    p = Path(root) / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _meta_line(meta: dict[str, Any]) -> str:
    return "｜".join([
        f"来源：{meta.get('source_document','')}",
        f"位置：{meta.get('location','')}",
        f"部件：{', '.join(meta.get('component_objects', []) or [])}",
        f"方面：{', '.join(meta.get('requirement_intents', []) or [])}",
        f"可支撑：{', '.join(meta.get('can_support', []) or [])}",
        f"强度：{meta.get('evidence_strength','')}",
        f"适用性：{meta.get('is_generalizable','')}/{meta.get('applicability_level','')}",
    ])


def save_pack(batch_dir: str | Path, payload: dict[str, Any]) -> Path:
    p = Path(batch_dir)
    p.mkdir(parents=True, exist_ok=True)
    json_path = p / "all_requirements_results.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = p / "all_requirements_results.md"
    lines = ["# 需求证据包（V2 工程字段版）", ""]
    for req in payload.get("requirements", []):
        lines.append(f"## {req.get('requirement_id')} {req.get('stakeholder')}")
        lines.append(req.get("raw_requirement_text", ""))
        lines.append("")
        for sub in req.get("sub_requirements", []):
            lines.append(f"### {sub.get('sub_requirement_id')} {sub.get('topic')}")
            lines.append(sub.get("text", ""))
            lines.append("")
            profile = sub.get("profile", {}) or {}
            lines.append(f"检索画像：部件={profile.get('target_components', [])}；方面={profile.get('target_aspects', [])}；可支撑={profile.get('required_can_support', [])}")
            lines.append("")
            if sub.get("evidence_gap"):
                gap = sub["evidence_gap"]
                lines.append("> 证据缺口：" + gap.get("reason", ""))
                lines.append("> 建议补充：" + gap.get("suggested_document_update", ""))
                lines.append("")
            for ev in sub.get("selected_results", []):
                meta = ev.get("metadata", {})
                judge = ev.get("llm_judge", {})
                lines.append(f"- {ev.get('id')}｜{judge.get('support_type','')}｜{judge.get('evidence_role','')}")
                lines.append(f"  - {_meta_line(meta)}")
                if meta.get("unsupported_requirements"):
                    lines.append(f"  - 不能支撑：{safe_text(meta.get('unsupported_requirements'))[:220]}")
                lines.append("```text")
                lines.append(ev.get("text", "")[:1600])
                lines.append("```")
                lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path
