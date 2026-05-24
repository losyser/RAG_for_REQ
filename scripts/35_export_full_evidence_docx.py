# -*- coding: utf-8 -*-
"""
Export all evidence_units.jsonl entries to evidence.docx,
organised by component (Heading 1) → aspect (Heading 2) → entry (Heading 3).
Mirrors the chapter structure of the original evidence.docx.
Backs up original before overwriting.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from docx import Document
from docx.shared import Pt

EU_PATH   = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl"
OUT_PATH  = PROJECT_ROOT / "data" / "raw" / "evidence.docx"
BAK_PATH  = PROJECT_ROOT / "data" / "raw" / "evidence_original.docx.bak"

# ── Chapter mapping: component → display title ────────────────
CHAPTER_ORDER = [
    ("main_engine_cooling_water_system", "01. 主机冷却水系统总体"),
    ("ht_cooling_water_loop",            "02. 高温冷却水回路"),
    ("lt_cooling_water_loop",            "03. 低温冷却水回路"),
    ("cooling_water_pump",               "04. 冷却水泵"),
    ("cooler",                           "05. 冷却器"),
    ("expansion_tank",                   "06. 膨胀水箱"),
    ("temperature_control_valve",        "07. 温控阀"),
    ("pipe",                             "08. 管路"),
    ("valve",                            "08b. 阀门"),
    ("sea_water_cooling_system",         "09a. 海水冷却系统"),
    ("central_cooling_system",           "09b. 中央冷却系统"),
    ("jacket_water_cooling_system",      "09c. 缸套水冷却系统"),
    ("temperature_sensor",               "10a. 温度传感器"),
    ("pressure_sensor",                  "10b. 压力传感器"),
    ("level_sensor",                     "10c. 液位传感器"),
    ("sensor",                           "10d. 传感器（通用）"),
    ("alarm_system",                     "11. 报警与保护"),
    ("control_system",                   "12. 控制系统"),
    ("coolant",                          "13. 冷却液与水质"),
    ("drain_point",                      "14a. 放水点"),
    ("vent_point",                       "14b. 排气点"),
    ("filter",                           "14c. 滤器"),
    ("equipment_interface",              "14d. 设备接口"),
    ("technical_file",                   "15. 图纸与文件"),
]
CHAPTER_MAP = {comp: title for comp, title in CHAPTER_ORDER}
KNOWN_COMPS = {comp for comp, _ in CHAPTER_ORDER}


def _list_field(val) -> str:
    if isinstance(val, list):
        return " / ".join(val) if val else ""
    return str(val) if val else ""


def _add_field(doc: Document, label: str, value: str) -> None:
    p = doc.add_paragraph(style="Normal")
    p.add_run(f"{label}：").bold = True
    p.add_run(value or "")


def _add_entry(doc: Document, unit: dict) -> None:
    m   = unit["metadata"]
    uid = unit["id"]

    doc.add_heading(f"{uid} {m.get('topic', '')}", level=3)

    _add_field(doc, "证据编号",    uid)
    _add_field(doc, "来源文档",    m.get("source_document", ""))
    _add_field(doc, "来源类型",    m.get("source_type", ""))
    _add_field(doc, "来源链接",    m.get("source_link", ""))
    _add_field(doc, "页码或位置",  m.get("location", ""))
    _add_field(doc, "章节标题",    m.get("section_title", ""))
    _add_field(doc, "系统层级",    _list_field(m.get("system_scope")))
    _add_field(doc, "部件对象",    _list_field(m.get("component_objects")))
    _add_field(doc, "相关提及对象", _list_field(m.get("related_objects")))
    _add_field(doc, "需求方面",    _list_field(m.get("requirement_intents")))
    _add_field(doc, "工程阶段",    _list_field(m.get("engineering_phase")))
    _add_field(doc, "适用工况",    _list_field(m.get("applicable_condition")))
    _add_field(doc, "可支撑类型",  _list_field(m.get("can_support")))
    _add_field(doc, "证据强度",    m.get("evidence_strength", ""))
    _add_field(doc, "是否可泛化",  m.get("is_generalizable", ""))
    _add_field(doc, "适用性等级",  m.get("applicability_level", ""))
    _add_field(doc, "适用厂家",    m.get("manufacturer", ""))
    _add_field(doc, "适用机型",    m.get("engine_model", ""))
    _add_field(doc, "适用系统型式", _list_field(m.get("system_type")))
    _add_field(doc, "是否需要人工复核", m.get("need_human_review", ""))
    _add_field(doc, "适用对象",    m.get("applicable_object", ""))
    _add_field(doc, "限制条件",    m.get("limitation", ""))

    # Quantitative parameters
    params = m.get("parameters") or []
    if params:
        p = doc.add_paragraph(style="Normal")
        p.add_run("量化参数：").bold = True
        for param in params:
            name  = param.get("name", "")
            val   = param.get("value", "")
            unit_ = param.get("unit", "")
            cond  = param.get("condition", "")
            line  = f"{name} = {val} {unit_}".strip()
            if cond:
                line += f"  [{cond}]"
            doc.add_paragraph(f"  • {line}", style="Normal")

    # Original text
    p = doc.add_paragraph(style="Normal")
    p.add_run("原文：").bold = True
    doc.add_paragraph(unit.get("text", ""), style="Normal")

    # Summary
    p = doc.add_paragraph(style="Normal")
    p.add_run("整理说明：").bold = True
    doc.add_paragraph(m.get("normalized_summary", ""), style="Normal")

    # Supportable requirements
    supportable = m.get("supportable_requirements") or []
    p = doc.add_paragraph(style="Normal")
    p.add_run("可支撑的需求：").bold = True
    if supportable:
        for i, item in enumerate(supportable, 1):
            if str(item).strip():
                doc.add_paragraph(f"{i}. {item}", style="Normal")

    # Unsupported requirements
    unsupported = m.get("unsupported_requirements") or ""
    p = doc.add_paragraph(style="Normal")
    p.add_run("不能支撑的需求：").bold = True
    if isinstance(unsupported, list):
        for i, item in enumerate(unsupported, 1):
            doc.add_paragraph(f"{i}. {item}", style="Normal")
    elif unsupported.strip():
        lines = [l.strip() for l in unsupported.split("\n") if l.strip()]
        for i, line in enumerate(lines, 1):
            doc.add_paragraph(f"{i}. {line}", style="Normal")

    # Keywords
    kw_zh = m.get("keywords_zh") or []
    kw_en = m.get("keywords_en") or []
    kw_all = kw_zh + kw_en
    if not kw_all:
        kw_all = (m.get("component_objects") or []) + (m.get("can_support") or [])[:3]
    _add_field(doc, "建议关联关键词", "，".join(kw_all))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    with open(EU_PATH, encoding="utf-8") as f:
        units = [json.loads(l) for l in f if l.strip()]
    print(f"Loaded {len(units)} evidence units")

    # ── Group units: primary_component → aspect → [units] ─────
    tree: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    unclassified: list[dict] = []
    for u in units:
        comps = u["metadata"].get("component_objects") or []
        # Find first recognised component
        primary = next((c for c in comps if c in KNOWN_COMPS), None)
        if primary is None:
            primary = comps[0] if comps else "unknown"
        aspects = u["metadata"].get("can_support") or ["other"]
        primary_aspect = aspects[0]
        tree[primary][primary_aspect].append(u)

    # ── Build document ─────────────────────────────────────────
    doc = Document()

    # Title + header
    t = doc.add_paragraph(style="Normal")
    r = t.add_run("船舶主机冷却水系统 RAG 工程证据库（整理版 V3）")
    r.bold = True
    r.font.size = Pt(14)

    doc.add_paragraph(
        "本文件由 evidence.docx 经去重整理（移除983条冗余）并补充10个权威来源后重新生成，"
        "格式与原版保持一致，按系统组件分章、按需求方面分节组织。",
        style="Normal"
    )
    doc.add_paragraph(
        f"生成时间：2026-05-24；证据条数：{len(units)}。",
        style="Normal"
    )

    # 0. 文档说明
    doc.add_heading("0. 文档说明与字段规范", level=1)
    doc.add_paragraph(
        "组织方式：按系统组件归章，并在组件章节内按需求方面（can_support）组织证据。",
        style="Normal"
    )
    doc.add_paragraph(
        "去重说明：对原2232条证据按文本前400字符指纹去重，保留直接证据（direct）优先、"
        "可支撑类型最丰富的代表性条目，去重后1249条。",
        style="Normal"
    )
    doc.add_paragraph(
        "补充说明：新增18条来自 IACS UR M3.1/M28/M51/M72/M73/E10、"
        "DNV Pt.4 Ch.3、CCS第4篇第3章、Wärtsilä 46DF实测参数的权威来源证据，"
        "重点填补 capacity 方面的全局空白。",
        style="Normal"
    )

    # Component directory
    doc.add_heading("组件目录", level=2)
    for comp, title in CHAPTER_ORDER:
        n = sum(len(v) for v in tree.get(comp, {}).values())
        if n > 0:
            doc.add_paragraph(f"{title}：{n} 条证据", style="Normal")

    # Coverage overview
    doc.add_heading("覆盖性概览", level=2)
    for comp, title in CHAPTER_ORDER:
        chapter_units = tree.get(comp, {})
        n = sum(len(v) for v in chapter_units.values())
        if n > 0:
            doc.add_paragraph(f"{title}：{n} 条证据", style="Normal")

    # ── Chapters ───────────────────────────────────────────────
    written_comps: set[str] = set()
    for comp, chapter_title in CHAPTER_ORDER:
        if comp not in tree:
            continue
        written_comps.add(comp)
        doc.add_heading(chapter_title, level=1)
        for aspect, aspect_units in sorted(tree[comp].items()):
            doc.add_heading(aspect, level=2)
            for u in aspect_units:
                _add_entry(doc, u)

    # Any component not in CHAPTER_ORDER goes to a misc chapter
    misc_comps = set(tree.keys()) - written_comps
    if misc_comps:
        doc.add_heading("附录. 其他组件", level=1)
        for comp in sorted(misc_comps):
            for aspect, aspect_units in sorted(tree[comp].items()):
                doc.add_heading(f"{comp} — {aspect}", level=2)
                for u in aspect_units:
                    _add_entry(doc, u)

    # ── Backup original and write ──────────────────────────────
    if OUT_PATH.exists() and not BAK_PATH.exists():
        shutil.copy2(OUT_PATH, BAK_PATH)
        print(f"Original backed up to: {BAK_PATH}")

    doc.save(OUT_PATH)
    import os
    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"Saved: {OUT_PATH}  ({size_kb} KB)")

    # Verify
    check = Document(OUT_PATH)
    h3s = sum(1 for p in check.paragraphs if p.style.name == 'Heading 3')
    print(f"Verification — Heading 3 entries: {h3s}  (expected {len(units)})")


if __name__ == "__main__":
    main()
