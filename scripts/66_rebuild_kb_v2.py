#!/usr/bin/env python3
"""
Script 66: KB v2 structural rebuild (Step 1+2, no LLM)

Changes per unit:
  ALL tiers  — rebuild concise search_text (template-based, ~20-60 chars vs old ~1000+)
  ALL tiers  — kb_tier int→str ("L1"/"L2"/"L3")
  ALL tiers  — promote evidence_strength, source_* fields to top level
  L1 only    — add constraint skeleton (all null, filled by LLM in script 67)

Output: data/processed/evidence_units_v2.jsonl
Original: data/processed/evidence_units.jsonl (untouched)
"""

import json
import re
from pathlib import Path

SRC  = Path("data/processed/evidence_units.jsonl")
DEST = Path("data/processed/evidence_units_v2.jsonl")

# ── Chinese translations for intent/component labels ─────────────────────────
INTENT_ZH = {
    "redundancy": "冗余备用",
    "alarm_protection": "报警保护",
    "alarm_response": "报警响应",
    "parameter_limit": "参数限值",
    "material_spec": "材料规格",
    "inspection_test": "检验试验",
    "inspection": "检查",
    "certification": "送审认证",
    "calculation": "计算验证",
    "installation_req": "安装布置",
    "operational_req": "运行操作",
    "composition": "系统组成",
    "monitoring": "监测",
    "maintenance": "维护",
    "accessibility": "可达性",
    "system_description": "系统描述",
    "configuration": "配置",
    "temperature": "温度",
    "pressure": "压力",
    "flow": "流量",
    "cleaning": "清洗",
    "water_quality": "水质",
    "specification": "规格参数",
    "design_requirement": "设计要求",
    "operation": "运行",
}

SOURCE_ABBREVS = [
    ("ABS Marine Vessel Rules Part 4", "ABS-P4"),
    ("ABS Rules for Building", "ABS"),
    ("ABS", "ABS"),
    ("CCS 海船入级规范", "CCS"),
    ("CCS", "CCS"),
    ("SOLAS", "SOLAS"),
    ("IACS UR", "IACS"),
    ("IACS", "IACS"),
    ("DNV-RU", "DNV"),
    ("DNV", "DNV"),
    ("Lloyd", "LR"),
    ("Bureau Veritas", "BV"),
    ("MAN L23/30DF", "MAN-L23/30DF"),
    ("MAN 49/60DF", "MAN-49/60DF"),
    ("MAN 32/44CR", "MAN-32/44CR"),
    ("MAN B&W", "MAN-B&W"),
    ("MAN Energy Solutions", "MAN"),
    ("MAN", "MAN"),
    ("Wärtsilä", "WRT"),
    ("Wartsila", "WRT"),
    ("Caterpillar", "CAT"),
    ("Cummins", "CUM"),
]


def abbreviate_source(doc: str) -> str:
    if not doc:
        return ""
    cleaned = re.sub(r"^S\d+\s+", "", doc).strip()
    for key, abbrev in SOURCE_ABBREVS:
        if key.lower() in cleaned.lower():
            return abbrev
    words = cleaned.split()
    return " ".join(words[:2]) if words else ""


def extract_numeric_tokens(text: str) -> list:
    """Pull concise value+unit strings from raw text (for L2 parameter context)."""
    patterns = [
        r"\d+\.?\d*\s*°[CF]",
        r"\d+\.?\d*\s*[kK][pP][aA]",
        r"\d+\.?\d*\s*[bB]ar",
        r"\d+\.?\d*\s*[lL]/[hH]",
        r"\d+\.?\d*\s*m[³3h/]+",
        r"[≥≤<>]\s*\d+\.?\d*",
        r"\d+\s*×\s*\d+",         # e.g. 2×100%
        r"\d+\.?\d*\s*%",
        r"\d+\.?\d*\s*kW",
        r"\d+\.?\d*\s*rpm",
    ]
    found = []
    for p in patterns:
        for m in re.findall(p, text):
            token = m.strip().replace(" ", "")
            if token not in found:
                found.append(token)
            if len(found) >= 4:
                return found
    return found


def _is_clause_number(s: str) -> bool:
    """True when string looks like a bare clause code, e.g. '7-25 1.6', '7-34', '7-27 表 4 主燃气轮机'."""
    if not s:
        return False
    # Starts with a digit → clause number pattern
    return bool(s) and s[0].isdigit()


def build_search_text(unit: dict) -> str:
    m   = unit.get("metadata", {})
    tier = unit.get("kb_tier")
    parts = []

    section = m.get("section_title", "").strip()
    topic   = m.get("topic", "").strip()

    if section and not _is_clause_number(section):
        # ① Normal case: section_title is descriptive (e.g. "海水冷却系统：报警 - 传感器配置")
        parts.append(section[:60])
    else:
        # ② CCS-style: section_title is a clause code → use topic as primary label,
        #    then append the clause code as a short reference
        if topic:
            parts.append(topic)
        if section:
            parts.append(section)  # e.g. "7-25 1.6" kept as secondary reference

    # ② Source abbreviation
    src_abbrev = abbreviate_source(m.get("source_document", ""))
    if src_abbrev:
        parts.append(src_abbrev)

    # ③ Manufacturer / engine model (makes parameters locatable)
    mfr   = (m.get("manufacturer") or "").strip()
    model = (m.get("engine_model") or "").strip()
    if mfr and mfr not in " ".join(parts):
        parts.append(mfr)
    if model:
        parts.append(model)

    # ④ Intent in English (keeps cross-lingual retrieval)
    intent_en = (unit.get("primary_intent") or "").strip()
    if intent_en:
        parts.append(intent_en)

    # ⑤ Tier-specific extras
    if tier == 1:
        src_type = m.get("source_type", "")
        if src_type in ("ship_rule", "class_rule", "standard"):
            parts.append("规范强制")

    elif tier == 2:
        nums = extract_numeric_tokens(unit.get("text", ""))
        parts.extend(nums)

    elif tier == 3:
        parts.append("背景")

    # Deduplicate while preserving order
    seen, deduped = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            deduped.append(p)

    return " ".join(deduped)


def make_constraint_skeleton() -> dict:
    """L1 constraint fields — all null; filled by LLM in script 67."""
    return {
        "规范依据":   None,   # e.g. "ABS Part4 §13.5.2"
        "规范版本":   None,   # e.g. "2021版"
        "强制级别":   None,   # 强制 / 推荐 / 禁止
        "约束类型":   None,   # redundancy / alarm_protection / parameter_limit / …
        "适用对象":   None,   # specific component or system
        "核心要求":   None,   # 1-2 sentences, SHALL statement
        "可接受标准": None,   # quantitative acceptance criterion (null if absent)
        "验证方式":   None,   # design_review / sea_trial / calculation / …
        "关联条文":   None,   # cross-refs explicitly in source text (null if absent)
        "适用船型":   None,   # ship type restriction (null = all)
        "_extraction_meta": {
            "core_req_source":          None,  # stated / inferred / absent
            "acceptance_criteria_source": None,
            "verification_source":       None,
            "mandatory_level_source":    None,
        },
    }


def rebuild_unit(unit: dict) -> dict:
    tier_int = unit.get("kb_tier")
    tier_str = {1: "L1", 2: "L2", 3: "L3"}.get(tier_int, str(tier_int))
    m = unit.get("metadata", {})

    out = {
        # ── Identity ──────────────────────────────────────────────────────────
        "id":             unit["id"],   # kept for backward compat with pipeline
        "unit_id":        unit["id"],   # new canonical name (updated for L1 in script 67)
        "original_id":    unit["id"],
        "parent_chunk_id": unit.get("parent_chunk_id", ""),

        # ── Classification ────────────────────────────────────────────────────
        "kb_tier":          tier_str,
        "kb_version":       "v2",
        "primary_component": unit.get("primary_component", ""),
        "primary_intent":    unit.get("primary_intent", ""),
        "evidence_strength": m.get("evidence_strength", ""),
        "tier_reason":       unit.get("tier_reason", ""),

        # ── Source (promoted from metadata) ───────────────────────────────────
        "source_type":     m.get("source_type", ""),
        "source_document": m.get("source_document", ""),
        "location":        m.get("location", ""),
        "manufacturer":    m.get("manufacturer", ""),
        "engine_model":    m.get("engine_model", ""),

        # ── Content ───────────────────────────────────────────────────────────
        "text":        unit.get("text", ""),
        "search_text": build_search_text(unit),  # rebuilt

        # ── Original metadata kept for backward compatibility ─────────────────
        "metadata": unit.get("metadata", {}),
    }

    # L1 only: add constraint skeleton
    if tier_str == "L1":
        out["constraint"] = make_constraint_skeleton()

    return out


def main():
    with open(SRC, encoding="utf-8") as f:
        units = [json.loads(l) for l in f if l.strip()]

    rebuilt = [rebuild_unit(u) for u in units]

    with open(DEST, "w", encoding="utf-8") as f:
        for u in rebuilt:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    # ── Statistics ────────────────────────────────────────────────────────────
    tier_counts = {"L1": 0, "L2": 0, "L3": 0}
    old_lens, new_lens = [], []

    for old, new in zip(units, rebuilt):
        t = new["kb_tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1
        old_lens.append(len(old.get("search_text", "")))
        new_lens.append(len(new["search_text"]))

    print(f"[OK] Written {len(rebuilt)} units -> {DEST}")
    print(f"  L1={tier_counts['L1']}  L2={tier_counts['L2']}  L3={tier_counts['L3']}")
    print()
    print("search_text length comparison:")
    print(f"  OLD  avg={sum(old_lens)/len(old_lens):.0f}  "
          f"min={min(old_lens)}  max={max(old_lens)}")
    print(f"  NEW  avg={sum(new_lens)/len(new_lens):.0f}  "
          f"min={min(new_lens)}  max={max(new_lens)}")
    print()

    # Sample comparisons
    for tier in ("L1", "L2", "L3"):
        old_u = next(u for u in units if u.get("kb_tier") == {"L1":1,"L2":2,"L3":3}[tier])
        new_u = next(u for u in rebuilt if u.get("kb_tier") == tier)
        print(f"── {tier} sample ──")
        print(f"  OLD ({len(old_u.get('search_text',''))} chars): "
              f"{old_u.get('search_text','')[:90]}…")
        print(f"  NEW ({len(new_u['search_text'])} chars): {new_u['search_text']}")
        print()

    # Verify constraint skeleton on first L1
    l1_sample = next(u for u in rebuilt if u.get("kb_tier") == "L1")
    print("── L1 constraint skeleton ──")
    print(json.dumps(l1_sample.get("constraint", {}), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
