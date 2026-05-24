from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import normalize_id, safe_text


def refine_group_id(entry: dict[str, Any]) -> str:
    metadata = normalize_v2_metadata(entry["metadata"])
    source = normalize_id(safe_text(metadata.get("source_document"))[:40])
    location = normalize_id(safe_text(metadata.get("location"))[:20])
    components = metadata.get("component_objects") or []
    aspects = metadata.get("requirement_intents") or []
    phases = metadata.get("engineering_phase") or []
    topic = safe_text(metadata.get("topic"))

    comp_part = "_".join([normalize_id(x) for x in components[:2]]) if components else "no_component"
    aspect_part = "_".join([normalize_id(x) for x in aspects[:2]]) if aspects else "no_aspect"
    phase_part = "_".join([normalize_id(x) for x in phases[:1]]) if phases else "no_phase"
    topic_part = normalize_id(topic[:20]) if topic else "untitled"
    return normalize_id("__".join([source, location, comp_part, aspect_part, phase_part, topic_part]))


def build_evidence_units(raw_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    for e in raw_entries:
        metadata = normalize_v2_metadata(dict(e.get("metadata", {}) or {}))
        metadata["refined_group_id"] = refine_group_id({"metadata": metadata})
        chunk_id = make_parent_chunk_id(metadata)

        original = safe_text(e.get("original_excerpt"))
        summary = safe_text(metadata.get("normalized_summary"))
        unsupported = safe_text(metadata.get("unsupported_requirements"))
        supportable = "\n".join(metadata.get("supportable_requirements", []) or [])

        text = "\n".join([
            safe_text(metadata.get("topic")),
            original,
            f"整理说明：{summary}" if summary else "",
            f"可支撑：{supportable}" if supportable else "",
            f"不能支撑：{unsupported}" if unsupported else "",
        ]).strip()

        search_parts = [
            safe_text(metadata.get("topic")),
            safe_text(metadata.get("section_title")),
            safe_text(metadata.get("source_document")),
            safe_text(metadata.get("source_type")),
            " ".join(metadata.get("system_scope", []) or []),
            " ".join(metadata.get("component_objects", []) or []),
            " ".join(metadata.get("related_objects", []) or []),
            " ".join(metadata.get("requirement_intents", []) or []),
            " ".join(metadata.get("engineering_phase", []) or []),
            " ".join(metadata.get("applicable_condition", []) or []),
            " ".join(metadata.get("can_support", []) or []),
            safe_text(metadata.get("evidence_strength")),
            safe_text(metadata.get("is_generalizable")),
            safe_text(metadata.get("applicability_level")),
            safe_text(metadata.get("manufacturer")),
            safe_text(metadata.get("engine_model")),
            " ".join(metadata.get("system_type", []) or []),
            safe_text(metadata.get("applicable_object")),
            safe_text(metadata.get("limitation")),
            summary,
            supportable,
            unsupported,
            " ".join(metadata.get("keywords_zh", []) or []),
            " ".join(metadata.get("keywords_en", []) or []),
            original,
        ]
        search_text = "\n".join([p for p in search_parts if safe_text(p)])

        units.append({
            "id": e["id"],
            "parent_chunk_id": chunk_id,
            "text": text,
            "search_text": search_text,
            "metadata": metadata,
        })

    return units


def make_parent_chunk_id(metadata: dict[str, Any]) -> str:
    source = normalize_id(safe_text(metadata.get("source_document"))[:50])
    comp = normalize_id("_".join((metadata.get("component_objects") or ["component"])[:2]))
    aspect = normalize_id("_".join((metadata.get("requirement_intents") or ["aspect"])[:2]))
    loc = normalize_id(safe_text(metadata.get("location"))[:20])
    return f"CH_{source}_{comp}_{aspect}_{loc}"


def build_source_chunks(units: list[dict[str, Any]], max_units_per_chunk: int = 8) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        buckets[unit["parent_chunk_id"]].append(unit)

    chunks: list[dict[str, Any]] = []
    for base_chunk_id, items in buckets.items():
        for part_idx in range(0, len(items), max_units_per_chunk):
            part = items[part_idx:part_idx + max_units_per_chunk]
            chunk_id = base_chunk_id if len(items) <= max_units_per_chunk else f"{base_chunk_id}_P{part_idx // max_units_per_chunk + 1:02d}"
            for item in part:
                item["parent_chunk_id"] = chunk_id

            metas = [normalize_v2_metadata(x.get("metadata", {})) for x in part]
            first = metas[0]

            topics = [safe_text(m.get("topic")) for m in metas if safe_text(m.get("topic"))]
            aspects = sorted({i for m in metas for i in (m.get("requirement_intents", []) or [])})
            components = sorted({i for m in metas for i in (m.get("component_objects", []) or [])})
            phases = sorted({i for m in metas for i in (m.get("engineering_phase", []) or [])})
            conditions = sorted({i for m in metas for i in (m.get("applicable_condition", []) or [])})
            can_support = sorted({i for m in metas for i in (m.get("can_support", []) or [])})
            systems = sorted({i for m in metas for i in (m.get("system_scope", []) or [])})
            strengths = sorted({safe_text(m.get("evidence_strength")) for m in metas if safe_text(m.get("evidence_strength"))})
            source_types = sorted({safe_text(m.get("source_type")) for m in metas if safe_text(m.get("source_type"))})

            # 单值代表字段：供 normalize_v2_metadata 和 _score_by_profile 正确读取
            _st_counter = Counter(safe_text(m.get("source_type")) for m in metas if safe_text(m.get("source_type")))
            source_type_repr = _st_counter.most_common(1)[0][0] if _st_counter else ""

            _APP_ORDER = {
                "class_rule": 0, "general_engineering": 1,
                "manufacturer_specific": 2, "project_specific": 3, "background_reference": 4,
            }
            _app_vals = [safe_text(m.get("applicability_level")) for m in metas
                         if safe_text(m.get("applicability_level")) not in {"", "unknown"}]
            app_level_repr = min(_app_vals, key=lambda x: _APP_ORDER.get(x, 5)) if _app_vals else "unknown"

            _GEN_ORDER = {"no": 0, "limited": 1, "yes": 2}
            _gen_vals = [safe_text(m.get("is_generalizable")) for m in metas
                         if safe_text(m.get("is_generalizable")) not in {"", "unknown"}]
            gen_repr = min(_gen_vals, key=lambda x: _GEN_ORDER.get(x, 3)) if _gen_vals else "unknown"

            chunk_text = "\n\n".join([f"{x['id']} {x['text']}" for x in part])
            search_text = "\n".join([
                " ".join(topics),
                " ".join(components),
                " ".join(aspects),
                " ".join(phases),
                " ".join(conditions),
                " ".join(can_support),
                " ".join(strengths),
                chunk_text,
            ])

            chunks.append({
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "search_text": search_text,
                "evidence_ids": [x["id"] for x in part],
                "metadata": {
                    "source_document": first.get("source_document", ""),
                    "location": first.get("location", ""),
                    "section_title": topics[0] if topics else "",
                    "source_types": source_types,
                    "source_type": source_type_repr,
                    "applicability_level": app_level_repr,
                    "is_generalizable": gen_repr,
                    "system_scope": systems,
                    "component_objects": components,
                    "evidence_types": aspects,
                    "requirement_intents": aspects,
                    "engineering_phase": phases,
                    "applicable_condition": conditions,
                    "can_support": can_support,
                    "evidence_strength": strengths[0] if len(strengths) == 1 else "mixed",
                },
            })
    return chunks


def build_evidence_groups(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        metadata = normalize_v2_metadata(unit.get("metadata", {}))
        comps = metadata.get("component_objects") or ["no_component"]
        aspects = metadata.get("requirement_intents") or ["no_aspect"]
        phase = (metadata.get("engineering_phase") or ["no_phase"])[0]
        gid = normalize_id(f"G_{comps[0]}__{aspects[0]}__{phase}")
        unit["metadata"]["refined_group_id"] = gid
        buckets[gid].append(unit)

    groups: list[dict[str, Any]] = []
    for gid, items in buckets.items():
        metas = [normalize_v2_metadata(x.get("metadata", {})) for x in items]
        topics = [safe_text(m.get("topic")) for m in metas if safe_text(m.get("topic"))]
        topic_counter = Counter(topics)
        group_topic = topic_counter.most_common(1)[0][0] if topic_counter else gid
        aspects = sorted({i for m in metas for i in (m.get("requirement_intents", []) or [])})
        components = sorted({i for m in metas for i in (m.get("component_objects", []) or [])})
        systems = sorted({i for m in metas for i in (m.get("system_scope", []) or [])})
        phases = sorted({i for m in metas for i in (m.get("engineering_phase", []) or [])})
        can_support = sorted({i for m in metas for i in (m.get("can_support", []) or [])})
        strengths = sorted({safe_text(m.get("evidence_strength")) for m in metas if safe_text(m.get("evidence_strength"))})
        summary = f"{group_topic}。包含 {len(items)} 条证据。部件：{', '.join(components) or '无'}。方面：{', '.join(aspects) or '无'}。"
        groups.append({
            "group_id": gid,
            "group_topic": group_topic,
            "group_summary": summary,
            "evidence_ids": [x["id"] for x in items],
            "metadata": {
                "system_scope": systems,
                "component_objects": components,
                "evidence_types": aspects,
                "requirement_intents": aspects,
                "engineering_phase": phases,
                "can_support": can_support,
                "evidence_strength": strengths,
            },
        })
    return groups


def build_review_markdown(
    raw_entries: list[dict[str, Any]],
    units: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    groups: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append("# 多粒度证据库审查文件（V2 部件化字段版）")
    lines.append("")
    lines.append(f"原始证据条目数：{len(raw_entries)}")
    lines.append(f"Evidence units：{len(units)}")
    lines.append(f"Source chunks：{len(chunks)}")
    lines.append(f"Evidence groups：{len(groups)}")
    lines.append("")

    object_counter = Counter()
    aspect_counter = Counter()
    support_counter = Counter()
    strength_counter = Counter()
    app_counter = Counter()
    for u in units:
        m = normalize_v2_metadata(u.get("metadata", {}))
        for obj in m.get("component_objects", []) or []:
            object_counter[obj] += 1
        for rel in m.get("requirement_intents", []) or []:
            aspect_counter[rel] += 1
        for s in m.get("can_support", []) or []:
            support_counter[s] += 1
        strength_counter[safe_text(m.get("evidence_strength"))] += 1
        app_counter[safe_text(m.get("applicability_level"))] += 1

    lines.append("## 部件统计")
    for k, v in object_counter.most_common():
        lines.append(f"- {k}：{v}")
    lines.append("")

    lines.append("## 需求方面统计")
    for k, v in aspect_counter.most_common():
        lines.append(f"- {k}：{v}")
    lines.append("")

    lines.append("## 可支撑类型统计")
    for k, v in support_counter.most_common():
        lines.append(f"- {k}：{v}")
    lines.append("")

    lines.append("## 证据强度统计")
    for k, v in strength_counter.most_common():
        lines.append(f"- {k}：{v}")
    lines.append("")

    lines.append("## 适用性等级统计")
    for k, v in app_counter.most_common():
        lines.append(f"- {k}：{v}")
    lines.append("")

    lines.append("## 过大证据组 Top 30")
    for g in sorted(groups, key=lambda x: len(x["evidence_ids"]), reverse=True)[:30]:
        lines.append(f"- {g['group_id']}｜{g['group_topic']}｜{len(g['evidence_ids'])} 条")
    lines.append("")

    lines.append("## 样例 Source Chunks")
    for c in chunks[:20]:
        lines.append(f"### {c['chunk_id']}")
        lines.append(f"来源：{c['metadata'].get('source_document')}｜{c['metadata'].get('location')}")
        lines.append(f"部件：{', '.join(c['metadata'].get('component_objects', []) or [])}")
        lines.append(f"方面：{', '.join(c['metadata'].get('requirement_intents', []) or [])}")
        lines.append(f"证据：{', '.join(c['evidence_ids'])}")
        lines.append("```text")
        lines.append(c["chunk_text"][:1200])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)
