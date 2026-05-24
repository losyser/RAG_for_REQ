from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import safe_text


@dataclass(frozen=True)
class ApplicabilityRuleConfig:
    reject_noise: bool = True
    patent_as_background: bool = True
    weak_source_types: set[str] = field(default_factory=lambda: {"paper", "patent", "unknown", ""})
    strong_source_types: set[str] = field(default_factory=lambda: {
        "standard", "ship_rule", "class_rule", "engine_manual",
        "project_guide", "installation_guide",
    })
    object_sensitive_types: set[str] = field(default_factory=lambda: {
        "redundancy", "configuration", "parameter", "alarm_protection",
        "control", "maintainability", "installation", "verification",
    })


# ─────────────────────────────────────────────
# 扩充的"不能支撑"关键词表
# ─────────────────────────────────────────────
_UNSUPPORTED_KEYWORD_GROUPS: list[tuple[list[str], list[str]]] = [
    # (需求侧关键词, 证据侧 unsupported 关键词)
    (["具体数值", "参数限值", "温度限值", "压力限值", "流量限值"], ["具体数值", "数值", "参数限值"]),
    (["持续时间", "时间要求"], ["持续时间", "时间"]),
    (["验收判据", "试验判据", "验收标准"], ["验收判据", "试验判据"]),
    (["施工安装", "现场安装", "安装工艺"], ["施工安装", "安装"]),
    (["冲洗", "系统冲洗"], ["冲洗"]),
    (["试压", "水压试验", "压力试验"], ["试压", "水压"]),
    (["图纸", "布置图", "原理图"], ["图纸", "审图"]),
    (["审图", "图纸审查"], ["审图"]),
    (["焊接空间", "焊接"], ["焊接空间", "焊接"]),
    (["操作空间", "检修空间"], ["操作空间", "检修空间"]),
    (["支架间距", "支吊架"], ["支架间距", "支架"]),
    (["停机后冷却", "停机冷却"], ["停机后冷却"]),
]


class ApplicabilityFilter:
    """
    基于 V2 工程字段的适用性过滤。

    改进：
    1. hard-reject 条件更全面（噪声、not_applicable、background+低适用性组合）
    2. score_delta 上限控制，避免叠加后分数异常
    3. unsupported_requirements 关键词匹配扩充
    4. 来源类型为 paper/patent 且 is_generalizable=no 时直接 hard-reject
    """

    def __init__(self, config: ApplicabilityRuleConfig | None = None):
        self.config = config or ApplicabilityRuleConfig()

    def apply(
        self,
        sub_requirement: dict[str, Any],
        candidates: list[dict[str, Any]],
        *,
        top_k_for_judge: int = 25,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        annotated: list[dict[str, Any]] = []
        hard_rejected: list[dict[str, Any]] = []

        for candidate in candidates:
            item = dict(candidate)
            item["metadata"] = normalize_v2_metadata(item.get("metadata", {}) or {})
            assessment = self.assess(sub_requirement, item)
            item["applicability"] = assessment

            # 更新 final_score（delta 已在 assess 中裁剪）
            current_score = float(item.get("final_score", 0.0) or 0.0)
            item["final_score"] = round(current_score + assessment["score_delta"], 4)

            if assessment["decision"] == "reject":
                hard_rejected.append(item)
            else:
                annotated.append(item)

        annotated.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        hard_rejected.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

        return annotated[:top_k_for_judge], hard_rejected

    def assess(
        self,
        sub_requirement: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        metadata = normalize_v2_metadata(candidate.get("metadata", {}) or {})
        profile_match = candidate.get("profile_match", {}) or {}
        requirement_type = safe_text(sub_requirement.get("requirement_type")) or "other"

        source_type = safe_text(metadata.get("source_type")).lower()
        evidence_strength = safe_text(metadata.get("evidence_strength")).lower()
        app_level = safe_text(metadata.get("applicability_level"))
        generalizable = safe_text(metadata.get("is_generalizable")).lower()
        unsupported = safe_text(metadata.get("unsupported_requirements"))
        is_noise = bool(metadata.get("is_noise"))

        item_aspects = set(metadata.get("requirement_intents", []) or [])
        item_can_support = set(metadata.get("can_support", []) or [])
        matched_components = set(profile_match.get("matched_components", []) or [])
        target_components = set(profile_match.get("target_components", []) or [])
        matched_aspects = set(profile_match.get("matched_aspects", []) or [])
        target_aspects = set(profile_match.get("target_aspects", []) or [])
        matched_can_support = set(profile_match.get("matched_can_support", []) or [])
        required_can_support = set(profile_match.get("required_can_support", []) or [])

        reasons: list[str] = []
        constraints: list[str] = []
        score_delta = 0.0
        decision = "pass"
        max_role = "primary"

        # ── Hard-reject 条件 ──

        # 1. 噪声
        if self.config.reject_noise and is_noise:
            return self._reject("metadata 标记为噪声证据。")

        # 2. 明确不适用
        if evidence_strength == "not_applicable":
            return self._reject("证据强度为 not_applicable。")

        # 3. background + background_reference 组合 → hard-reject
        if evidence_strength == "background" and app_level == "background_reference":
            return self._reject("证据强度为 background 且适用性等级为 background_reference，不送审。")

        # 4. paper/patent + is_generalizable=no → 对工程类需求 hard-reject
        if source_type in {"paper", "patent"} and generalizable == "no":
            if requirement_type in self.config.object_sensitive_types:
                return self._reject(f"来源为 {source_type} 且不可泛化，不适用于工程约束类需求。")

        # ── Score delta 计算 ──

        # 证据强度
        if evidence_strength == "background":
            score_delta -= 0.60
            max_role = self._lower_role(max_role, "background")
            constraints.append("证据强度为 background，只能作为背景，不宜作为工程主证据。")
        elif evidence_strength == "direct":
            score_delta += 0.20
        elif evidence_strength == "indirect":
            score_delta += 0.05
            max_role = self._lower_role(max_role, "supporting")

        # 来源类型
        if source_type in {"paper", "patent"}:
            score_delta -= 0.40
            max_role = self._lower_role(max_role, "background")
            reasons.append(f"来源类型为 {source_type}，不能单独作为工程强制要求。")
        elif source_type in {"ship_rule", "class_rule", "standard"}:
            score_delta += 0.25
            reasons.append("来源为规则或标准，工程权重较高。")
        elif source_type in {"project_guide", "engine_manual", "installation_guide"}:
            score_delta += 0.15
            reasons.append("来源为厂家或安装指南，需受厂家和机型边界限制。")

        # 泛化性
        if generalizable == "no":
            score_delta -= 0.35
            max_role = self._lower_role(max_role, "background")
            constraints.append("证据标记为不可泛化，不能跨厂家、机型或系统型式使用。")
        elif generalizable == "limited":
            score_delta -= 0.05
            constraints.append("证据适用性为 limited，应保留厂家、机型和系统型式限制。")

        # 适用性等级
        if app_level == "background_reference":
            score_delta -= 0.40
            max_role = self._lower_role(max_role, "background")
        elif app_level in {"class_rule", "general_engineering"}:
            score_delta += 0.20
        elif app_level in {"manufacturer_specific", "project_specific"}:
            score_delta += 0.05

        # 部件匹配（object_sensitive 类型才严格检查）
        if requirement_type in self.config.object_sensitive_types:
            if target_components and not matched_components:
                if "main_engine_cooling_water_system" not in (profile_match.get("item_components") or []):
                    score_delta -= 0.30
                    max_role = self._lower_role(max_role, "supporting")
                    constraints.append("目标部件未匹配，不能作为 direct 主证据。")

        # 方面匹配
        if target_aspects and not matched_aspects:
            score_delta -= 0.25
            max_role = self._lower_role(max_role, "supporting")
            constraints.append("需求方面未匹配，证据支撑能力降低。")

        # can_support 匹配
        if required_can_support and not matched_can_support:
            score_delta -= 0.25
            max_role = self._lower_role(max_role, "supporting")
            constraints.append("可支撑类型未匹配，不能作为主要工程依据。")

        # 安装类专属检查
        if requirement_type == "installation":
            install_support = {"installation", "arrangement", "inspection", "test", "flushing", "pressure_test"}
            if not (item_can_support & install_support):
                score_delta -= 0.30
                max_role = self._lower_role(max_role, "background")
                constraints.append("施工安装类需求需要 installation、arrangement、inspection、flushing 或 pressure_test 类证据。")

        # 参数类专属检查
        if requirement_type == "parameter":
            param_aspects = {"temperature", "pressure", "flow", "capacity", "monitoring", "parameter_limit"}
            if not (item_aspects & param_aspects):
                score_delta -= 0.25
                max_role = self._lower_role(max_role, "supporting")
                constraints.append("参数类需求需要温度、压力、流量、容量或监测类证据。")

        # unsupported_requirements 命中检查（扩充关键词）
        if unsupported:
            req_text = " ".join([
                safe_text(sub_requirement.get("topic")),
                safe_text(sub_requirement.get("text")),
            ])
            hit = self._unsupported_hits(req_text, unsupported)
            if hit:
                score_delta -= 0.70
                max_role = self._lower_role(max_role, "background")
                constraints.append(f"证据的【不能支撑的需求】命中当前需求：{hit}。禁止判为 direct。")

        # 正向奖励（匹配加分）
        if matched_components:
            score_delta += 0.08
        if matched_aspects:
            score_delta += 0.10
        if matched_can_support:
            score_delta += 0.10

        if not reasons:
            reasons.append("未发现明显来源层面的适用性问题。")

        # score_delta 裁剪：避免叠加后过于极端
        score_delta = max(-1.50, min(0.80, score_delta))

        return {
            "decision": decision,
            "max_role": max_role,
            "score_delta": round(score_delta, 4),
            "reasons": reasons,
            "constraints": constraints,
        }

    @staticmethod
    def _reject(reason: str) -> dict[str, Any]:
        return {
            "decision": "reject",
            "max_role": "not_applicable",
            "score_delta": -2.0,
            "reasons": [reason],
            "constraints": [],
        }

    @staticmethod
    def _unsupported_hits(req_text: str, unsupported: str) -> str:
        """返回命中的关键词对描述，未命中返回空字符串。"""
        req_lower = req_text.lower()
        unsupported_lower = unsupported.lower()
        for req_keys, ev_keys in _UNSUPPORTED_KEYWORD_GROUPS:
            req_hit = any(k.lower() in req_lower for k in req_keys)
            ev_hit = any(k.lower() in unsupported_lower for k in ev_keys)
            if req_hit and ev_hit:
                matched_req = next((k for k in req_keys if k.lower() in req_lower), "")
                matched_ev = next((k for k in ev_keys if k.lower() in unsupported_lower), "")
                return f"需求关键词「{matched_req}」命中证据不能支撑「{matched_ev}」"
        return ""

    @staticmethod
    def _lower_role(current: str, target: str) -> str:
        order = {"primary": 0, "supporting": 1, "background": 2, "not_applicable": 3}
        return target if order.get(target, 0) > order.get(current, 0) else current