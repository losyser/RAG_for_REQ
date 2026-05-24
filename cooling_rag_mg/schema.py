from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, Field


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def split_list(value: Any) -> list[str]:
    """兼容 V2 docx 中用 /、逗号、分号分隔的字段。"""
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(split_list(item))
        return unique_keep_order(out)
    text = _safe_text(value)
    if not text or text in {"无", "-", "—", "N/A", "n/a"}:
        return []
    parts = re.split(r"\s*(?:/|,|，|;|；|、|\n)\s*", text)
    return unique_keep_order([p.strip() for p in parts if p.strip() and p.strip() not in {"无", "-", "—"}])


def unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = _safe_text(item)
        if not key or key in seen:
            continue
        out.append(key)
        seen.add(key)
    return out


V2_METADATA_FIELDS = [
    "source_document",
    "source_type",
    "source_link",
    "location",
    "section_title",
    "system_scope",
    "component_objects",
    "related_objects",
    "requirement_intents",
    "engineering_phase",
    "applicable_condition",
    "can_support",
    "evidence_strength",
    "is_generalizable",
    "applicability_level",
    "manufacturer",
    "engine_model",
    "system_type",
    "need_human_review",
    "applicable_object",
    "limitation",
    "normalized_summary",
    "supportable_requirements",
    "unsupported_requirements",
    "keywords_zh",
    "keywords_en",
]


def normalize_v2_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """统一 evidence.docx 的字段。

    旧版字段仍兼容：objects -> component_objects，relations -> requirement_intents。
    后续检索、适用性过滤和证据审查都应先调用本函数。
    """

    m: dict[str, Any] = dict(metadata or {})

    # 基础来源字段
    m["source_document"] = _safe_text(m.get("source_document") or m.get("来源文档"))
    m["source_type"] = _safe_text(m.get("source_type") or m.get("来源类型")).lower()
    m["source_link"] = _safe_text(m.get("source_link") or m.get("来源链接"))
    m["location"] = _safe_text(m.get("location") or m.get("页码或位置") or m.get("位置"))
    m["section_title"] = _safe_text(m.get("section_title") or m.get("章节标题"))
    m["topic"] = _safe_text(m.get("topic") or m.get("证据标题"))

    # V2 工程字段
    m["system_scope"] = split_list(m.get("system_scope") or m.get("系统层级"))
    m["component_objects"] = split_list(
        m.get("component_objects") or m.get("objects") or m.get("部件对象")
    )
    m["related_objects"] = split_list(m.get("related_objects") or m.get("相关提及对象"))
    m["requirement_intents"] = split_list(
        m.get("requirement_intents") or m.get("relations") or m.get("需求方面")
    )
    m["engineering_phase"] = split_list(m.get("engineering_phase") or m.get("工程阶段"))
    m["applicable_condition"] = split_list(m.get("applicable_condition") or m.get("适用工况"))
    m["can_support"] = split_list(m.get("can_support") or m.get("可支撑类型"))

    m["evidence_strength"] = _safe_text(m.get("evidence_strength") or m.get("证据强度") or "unknown").lower()
    m["is_generalizable"] = _safe_text(m.get("is_generalizable") or m.get("是否可泛化") or "unknown").lower()
    m["applicability_level"] = _safe_text(m.get("applicability_level") or m.get("适用性等级") or "unknown")
    m["manufacturer"] = _safe_text(m.get("manufacturer") or m.get("适用厂家"))
    m["engine_model"] = _safe_text(m.get("engine_model") or m.get("适用机型"))
    m["system_type"] = split_list(m.get("system_type") or m.get("适用系统型式"))
    m["need_human_review"] = _safe_text(m.get("need_human_review") or m.get("是否需要人工复核") or "no").lower()
    m["applicable_object"] = _safe_text(m.get("applicable_object") or m.get("适用对象"))
    m["limitation"] = _safe_text(m.get("limitation") or m.get("限制条件"))

    # 说明类字段
    m["normalized_summary"] = _safe_text(m.get("normalized_summary") or m.get("整理说明"))
    m["supportable_requirements"] = split_list(m.get("supportable_requirements") or m.get("可支撑的需求"))
    unsupported = m.get("unsupported_requirements") or m.get("不能支撑的需求") or ""
    if isinstance(unsupported, list):
        m["unsupported_requirements"] = "\n".join([_safe_text(x) for x in unsupported if _safe_text(x)])
    else:
        m["unsupported_requirements"] = _safe_text(unsupported)

    m["keywords_zh"] = split_list(m.get("keywords_zh") or m.get("建议关联关键词"))
    m["keywords_en"] = split_list(m.get("keywords_en"))

    # 兼容旧字段
    m["objects"] = m["component_objects"]
    m["relations"] = m["requirement_intents"]
    if not m.get("answer_type") and m["requirement_intents"]:
        m["answer_type"] = m["requirement_intents"][0]

    return m


class EvidenceUnit(BaseModel):
    id: str
    parent_chunk_id: str
    text: str
    search_text: str
    metadata: dict[str, Any]


class SourceChunk(BaseModel):
    chunk_id: str
    chunk_text: str
    search_text: str
    metadata: dict[str, Any]
    evidence_ids: list[str] = Field(default_factory=list)


class EvidenceGroup(BaseModel):
    group_id: str
    group_topic: str
    group_summary: str
    evidence_ids: list[str]
    metadata: dict[str, Any]


class SubRequirement(BaseModel):
    sub_id: str
    requirement_type: str
    topic: str
    text: str


class RetrievalProfile(BaseModel):
    target_systems: list[str] = Field(default_factory=list)
    target_components: list[str] = Field(default_factory=list)
    target_aspects: list[str] = Field(default_factory=list)
    target_phases: list[str] = Field(default_factory=list)
    target_conditions: list[str] = Field(default_factory=list)
    required_can_support: list[str] = Field(default_factory=list)
    preferred_evidence_strength: list[str] = Field(default_factory=list)
    preferred_applicability: list[str] = Field(default_factory=list)
    intent: str = "other"
    must_have_any: list[str] = Field(default_factory=list)
    positive_keywords: list[str] = Field(default_factory=list)
    preferred_evidence_types: list[str] = Field(default_factory=list)
    negative_evidence_types: list[str] = Field(default_factory=list)


class JudgedEvidence(BaseModel):
    id: str
    support_type: Literal["direct", "indirect", "background", "not_applicable"]
    evidence_role: Literal["primary", "supporting", "verification", "risk", "reference", "context"]
    relevance: Literal["high", "medium", "low"]
    reason: str
