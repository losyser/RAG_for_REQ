"""
将 exp_v4/rag_v4_results.json 的工程化需求导出为 M-design（华望）XMI 格式。

输出：data/search_results/exp_v4/rag_v4_requirements_mdesign.xml
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cooling_rag_mg.mdesign_exporter import export_to_mdesign_file

# ── 路径 ──────────────────────────────────────────────────────────────────────
INPUT = Path(__file__).parent.parent / "data/search_results/exp_v4/rag_v4_results.json"
OUTPUT = Path(__file__).parent.parent / "data/search_results/exp_v4/rag_v4_requirements_mdesign.xml"


def _topic(shall: str, n: int) -> str:
    """取 shall 前 16 字作为需求名，截在最近的标点边界。"""
    text = shall.strip()
    if len(text) <= 16:
        return text
    # 在前 16 字内找最近的标点
    for i in range(16, 8, -1):
        if text[i] in "，。；、（）【】":
            return text[:i]
    return text[:16]


def _full_text(er: dict) -> str:
    """组合 shall + 可测量指标 + Grade + 引用 → M-design Text 字段。"""
    parts = [er.get("shall_statement", "").strip()]

    criterion = (er.get("measurable_criterion") or "").strip()
    if criterion:
        parts.append(f"可测量指标：{criterion}")

    condition = (er.get("applicable_condition") or "").strip()
    if condition:
        parts.append(f"适用条件：{condition}")

    grade = er.get("_grade", "")
    verif = (er.get("verification_method") or "").strip()
    if grade or verif:
        parts.append(f"[Grade {grade}] 验证方式：{verif}")

    citations = er.get("evidence_citations") or []
    for c in citations:
        tier = c.get("tier", "")
        src = c.get("source", "")
        clause = c.get("has_clause", "")
        line = f"引用（{tier}）{src}"
        if clause:
            line += f" — {clause}"
        parts.append(line)

    return " | ".join(parts)


def convert(data: dict) -> dict:
    """将 rag_v4_results.json 转换为 export_to_mdesign 所需的 payload 格式。"""
    requirement_sets = []
    for rs in data.get("result_sets", []):
        src_id = rs.get("source_requirement_id", "")
        ers_raw = rs.get("engineering_requirements") or []

        engineering_requirements = []
        for j, er in enumerate(ers_raw, start=1):
            shall = er.get("shall_statement", "")
            ev_ids = [c.get("kb_id", "") for c in (er.get("evidence_citations") or []) if c.get("kb_id")]
            engineering_requirements.append({
                "id": f"{src_id}-ER{j}",
                "topic": _topic(shall, j),
                "shall_statement": _full_text(er),
                "verification_method": er.get("verification_method", ""),
                "evidence_ids": ev_ids,
                "_grade": er.get("_grade", ""),
            })

        requirement_sets.append({
            "requirement_set_id": f"RS-{src_id}",
            "source_requirement_id": src_id,
            "professional_summary": rs.get("stakeholder", ""),
            "engineering_requirements": engineering_requirements,
        })

    return {"requirement_sets": requirement_sets}


def main() -> None:
    if not INPUT.exists():
        print(f"[ERROR] 找不到输入文件：{INPUT}")
        sys.exit(1)

    data = json.loads(INPUT.read_text("utf-8"))
    payload = convert(data)

    n_sets = len(payload["requirement_sets"])
    n_ers = sum(len(rs["engineering_requirements"]) for rs in payload["requirement_sets"])
    print(f"转换完成：{n_sets} 个需求集，共 {n_ers} 条工程化需求")

    out = export_to_mdesign_file(payload, OUTPUT, project_name="冷却水系统工程需求（v4 RAG）")
    print(f"M-design XML 已写入：{out}")
    print(f"文件大小：{out.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
