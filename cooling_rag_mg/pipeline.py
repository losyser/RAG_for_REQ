from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from cooling_rag_mg.applicability_filter import ApplicabilityFilter
from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_judge import apply_judge, judge_evidence
from cooling_rag_mg.retrieval_engine import MultiGranularRetriever
from cooling_rag_mg.requirement_splitter import split_requirement
from cooling_rag_mg.schema import normalize_v2_metadata


class Splitter(Protocol):
    def __call__(self, requirement_id: str, stakeholder: str, raw_text: str) -> list[dict[str, Any]]: ...


class Judge(Protocol):
    def __call__(self, sub_requirement: dict[str, Any], candidates: list[dict[str, Any]], max_selected: int = 5) -> dict[str, Any]: ...


@dataclass
class PipelineServices:
    retriever: MultiGranularRetriever
    splitter: Splitter = split_requirement
    judge: Judge = judge_evidence
    applicability_filter: ApplicabilityFilter = field(default_factory=ApplicabilityFilter)


def make_retriever() -> MultiGranularRetriever:
    cfg = get_config()
    return MultiGranularRetriever(
        source_index_dir=str(cfg.paths.indexes_dir / "source_chunks"),
        evidence_index_dir=str(cfg.paths.indexes_dir / "evidence_units"),
        evidence_units_path=str(cfg.paths.evidence_units_jsonl),
        evidence_groups_path=str(cfg.paths.evidence_groups_jsonl),
        device=cfg.model.device,
    )


def make_services() -> PipelineServices:
    return PipelineServices(retriever=make_retriever())


def run_requirements(requirements: list[dict[str, Any]], *, top_k: int = 5, coarse_k: int = 12, fine_k: int = 40) -> dict[str, Any]:
    return run_requirements_with_services(requirements, services=make_services(), top_k=top_k, coarse_k=coarse_k, fine_k=fine_k)


def run_requirements_with_services(
    requirements: list[dict[str, Any]],
    *,
    services: PipelineServices,
    top_k: int = 5,
    coarse_k: int = 12,
    fine_k: int = 40,
    judge_candidate_k: int = 25,
) -> dict[str, Any]:
    out_requirements = []
    diagnostics = {
        "requirement_count": len(requirements),
        "sub_requirement_count": 0,
        "selected_evidence_count": 0,
        "direct_evidence_count": 0,
        "indirect_evidence_count": 0,
        "background_evidence_count": 0,
        "evidence_gap_count": 0,
    }

    for req in requirements:
        rid = req["requirement_id"]
        stakeholder = req.get("stakeholder", "")
        raw_text = req.get("requirement_text", "")
        subs = services.splitter(rid, stakeholder, raw_text)
        out_subs = []

        for idx, sub in enumerate(subs, start=1):
            sub_payload = build_sub_payload(rid, idx, sub)
            stage = run_sub_requirement_stage(
                sub_payload,
                services=services,
                top_k=top_k,
                coarse_k=coarse_k,
                fine_k=fine_k,
                judge_candidate_k=judge_candidate_k,
            )
            diagnostics["sub_requirement_count"] += 1
            diagnostics["selected_evidence_count"] += len(stage["selected_results"])
            for ev in stage["selected_results"]:
                stype = (ev.get("llm_judge", {}) or {}).get("support_type", "")
                if stype == "direct":
                    diagnostics["direct_evidence_count"] += 1
                elif stype == "indirect":
                    diagnostics["indirect_evidence_count"] += 1
                elif stype == "background":
                    diagnostics["background_evidence_count"] += 1
            if stage["evidence_gap"]:
                diagnostics["evidence_gap_count"] += 1
            out_subs.append(stage)

        out_requirements.append({
            "requirement_id": rid,
            "stakeholder": stakeholder,
            "raw_requirement_text": raw_text,
            "sub_requirements": out_subs,
        })

    return {"requirements": out_requirements, "diagnostics": diagnostics}


def build_sub_payload(requirement_id: str, idx: int, sub: dict[str, Any]) -> dict[str, Any]:
    sub_raw_id = sub.get("sub_id") or f"{idx:02d}"
    sub_id = f"{requirement_id}-{str(sub_raw_id).zfill(2)}"
    return {
        "sub_requirement_id": sub_id,
        "requirement_type": sub.get("requirement_type", "other"),
        "topic": sub.get("topic", ""),
        "text": sub.get("text", ""),
        "split_method": sub.get("split_method", ""),
        "split_error": sub.get("split_error", ""),
        "source_phrase": sub.get("source_phrase", ""),
        "implication_type": sub.get("implication_type", ""),
    }


def run_sub_requirement_stage(
    sub_payload: dict[str, Any],
    *,
    services: PipelineServices,
    top_k: int,
    coarse_k: int,
    fine_k: int,
    judge_candidate_k: int,
) -> dict[str, Any]:
    retrieval = services.retriever.search_sub_requirement(sub_payload, top_k=top_k, coarse_k=coarse_k, fine_k=fine_k)
    applicable_candidates, applicability_rejected = services.applicability_filter.apply(
        sub_payload,
        retrieval["candidate_results"],
        top_k_for_judge=judge_candidate_k,
    )
    judge_result = services.judge(sub_payload, applicable_candidates, max_selected=top_k)
    selected, judge_rejected = apply_judge(applicable_candidates, judge_result)
    rejected = merge_rejected_results(judge_rejected, applicability_rejected)
    evidence_gap = build_evidence_gap(
        sub_payload=sub_payload,
        retrieval=retrieval,
        applicable_candidates=applicable_candidates,
        selected=selected,
        judge_result=judge_result,
        applicability_rejected=applicability_rejected,
    )
    return {
        **sub_payload,
        "retrieval_query": retrieval["query"],
        "profile": retrieval["profile"],
        "coarse_results": simplify_results(retrieval["coarse_results"], text_key="chunk_text"),
        "candidate_results": simplify_results(applicable_candidates),
        "selected_results": simplify_results(selected),
        "rejected_results": simplify_results(rejected),
        "evidence_gap": evidence_gap,
        "judge_result": judge_result,
        "stage_diagnostics": {
            "raw_candidate_count": len(retrieval["candidate_results"]),
            "applicable_candidate_count": len(applicable_candidates),
            "applicability_rejected_count": len(applicability_rejected),
            "selected_count": len(selected),
            "judge_method": judge_result.get("judge_method", ""),
        },
    }


def merge_rejected_results(judge_rejected: list[dict[str, Any]], applicability_rejected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in judge_rejected + applicability_rejected:
        rid = str(item.get("id") or item.get("chunk_id") or "")
        if not rid or rid in seen:
            continue
        if item in applicability_rejected and not item.get("llm_judge"):
            item = dict(item)
            item["llm_judge"] = {"id": rid, "support_type": "not_applicable", "reason": "工程适用性过滤未通过。"}
        out.append(item)
        seen.add(rid)
    return out


def build_evidence_gap(
    *,
    sub_payload: dict[str, Any],
    retrieval: dict[str, Any],
    applicable_candidates: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    judge_result: dict[str, Any],
    applicability_rejected: list[dict[str, Any]],
) -> dict[str, Any] | None:
    # 只有 direct 才算有可支撑证据。indirect 和 background 均生成 evidence_gap。
    direct_selected = [
        ev for ev in selected
        if (ev.get("llm_judge", {}) or {}).get("support_type") == "direct"
    ]
    if direct_selected:
        return None

    raw_candidates = retrieval.get("candidate_results", []) or []
    rejected = judge_result.get("rejected", []) or []
    profile = retrieval.get("profile", {}) or {}

    if not raw_candidates:
        gap_type = "no_candidate"
        reason = "检索阶段没有召回候选证据。"
        suggested = "检查索引是否建立完整，或补充该主题相关证据。"
    elif raw_candidates and not applicable_candidates:
        gap_type = "applicability_filtered_all"
        reason = "检索召回了候选证据，但 V2 工程适用性过滤后没有可送审证据。"
        suggested = "补充与目标部件、需求方面、工程阶段和可支撑类型更匹配的证据。"
    elif selected:
        # selected 非空但无 direct 证据
        indirect_selected = [
            ev for ev in selected
            if (ev.get("llm_judge", {}) or {}).get("support_type") == "indirect"
        ]
        if indirect_selected:
            gap_type = "only_indirect"
            reason = "只有间接证据，尚无直接证据形成工程化需求依据。"
            suggested = "补充规则条款原文、厂家 Technical Data、安装指南或试验程序等直接证据以确认工程要求。"
        else:
            gap_type = "only_background"
            reason = "只有 background 证据，不能形成工程化需求依据。"
            suggested = "补充规则、厂家技术数据、安装指南、试验程序或项目计算书等直接证据。"
    elif rejected:
        gap_type = classify_rejected_gap(sub_payload, applicable_candidates, rejected, applicability_rejected, profile)
        reason = build_gap_reason(gap_type)
        suggested = build_gap_suggestion(gap_type)
    else:
        gap_type = "judge_selected_none"
        reason = "候选证据已送入审查，但没有证据被判定为可支撑。"
        suggested = "查看 judge_result 和 candidate_results，判断是审查过严还是证据库覆盖不足。"

    return {
        "evidence_status": "evidence_gap",
        "gap_type": gap_type,
        "reason": reason,
        "suggested_document_update": suggested,
        "target_components": profile.get("target_components", []),
        "target_aspects": profile.get("target_aspects", []),
        "target_phases": profile.get("target_phases", []),
        "required_can_support": profile.get("required_can_support", []),
        "candidate_count": len(raw_candidates),
        "applicable_candidate_count": len(applicable_candidates),
        "rejected_by_judge_count": len(rejected),
        "rejected_by_applicability_count": len(applicability_rejected),
    }


def classify_rejected_gap(sub_payload: dict[str, Any], applicable_candidates: list[dict[str, Any]], rejected: list[dict[str, Any]], applicability_rejected: list[dict[str, Any]], profile: dict[str, Any]) -> str:
    if not applicable_candidates and applicability_rejected:
        return "applicability_filtered_all"
    rtype = sub_payload.get("requirement_type", "")
    if rtype == "installation":
        return "installation_evidence_gap"
    if rtype == "verification":
        return "verification_document_gap"
    if rtype == "parameter":
        return "parameter_source_gap"
    if rtype in {"control", "alarm_protection"}:
        return "control_alarm_evidence_gap"
    return "judge_rejected_all"


def build_gap_reason(gap_type: str) -> str:
    mapping = {
        "judge_rejected_all": "有候选证据，但均未达到直接或间接支撑标准。",
        "installation_evidence_gap": "当前证据库缺少与施工安装、管路布置、焊接空间、冲洗或试压直接相关的证据。",
        "verification_document_gap": "当前证据库缺少图纸、计算书、试验程序、审查清单或验收记录类证据。",
        "parameter_source_gap": "当前证据库缺少厂家技术数据、计算书或试验文件来确认参数限值。",
        "control_alarm_evidence_gap": "当前证据库缺少控制逻辑、报警阈值、传感器配置或试验验证类证据。",
        "applicability_filtered_all": "候选证据被工程适用性规则过滤，不能作为有效支撑。",
        "only_indirect": "仅有间接证据，缺少能直接给出参数限值、规则义务或操作步骤的直接证据。",
        "only_background": "只有背景证据，缺少可直接或间接支撑工程要求的证据。",
    }
    return mapping.get(gap_type, "当前证据库没有找到可支撑该子需求的证据。")


def build_gap_suggestion(gap_type: str) -> str:
    mapping = {
        "judge_rejected_all": "补充更直接的标准条款、厂家手册、试验记录或设计说明。",
        "installation_evidence_gap": "优先补充船舶管系施工规范、管路布置标准、支吊架标准、冲洗和压力试验程序。",
        "verification_document_gap": "补充系统原理图、管路布置图、热平衡计算书、流量和压降计算书、船级社送审清单。",
        "parameter_source_gap": "补充主机厂家 Technical Data、泵曲线、冷却器选型计算书、流量和压降计算书。",
        "control_alarm_evidence_gap": "补充控制逻辑说明、报警保护清单、I/O 表、传感器选型和功能试验大纲。",
        "applicability_filtered_all": "补充适用机型、适用系统范围和权威等级更匹配的证据。",
        "only_indirect": "补充规则原文条款、主机厂家 Technical Data、安装指南或试验程序等直接证据。",
        "only_background": "补充规则、厂家文件、项目计算书、试验程序或安装规范。",
    }
    return mapping.get(gap_type, "建议补充相关标准、船级社规则、主机手册、安装指南或试验记录。")


def simplify_results(results: list[dict[str, Any]], text_key: str = "text") -> list[dict[str, Any]]:
    out = []
    for r in results:
        meta = normalize_v2_metadata(r.get("metadata", {}) or {})
        out.append({
            "id": r.get("id") or r.get("chunk_id"),
            "text": r.get(text_key, r.get("text", "")),
            "metadata": meta,
            "final_score": r.get("final_score"),
            "rrf_score": r.get("rrf_score"),
            "profile_score": r.get("profile_score"),
            "coarse_chunk_hit": r.get("coarse_chunk_hit"),
            "expanded_from_group": r.get("expanded_from_group"),
            "retrieval_role": r.get("retrieval_role", ""),
            "profile_match": r.get("profile_match", {}),
            "applicability": r.get("applicability", {}),
            "llm_judge": r.get("llm_judge", {}),
        })
    return out
