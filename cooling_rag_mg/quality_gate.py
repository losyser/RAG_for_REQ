# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from cooling_rag_mg.config import get_config
from cooling_rag_mg.text_utils import safe_text

# ─────────────────────────────────────────────
# 模糊词表
# ─────────────────────────────────────────────
_VAGUE_ZH = [
    "按要求", "满足要求", "适当", "足够", "合适", "适宜", "较高", "较低",
    "较大", "较小", "良好", "合理", "相关", "一定",
    "尽量", "尽可能", "必要时", "必要的",
    # NOTE: "稳定" and "可靠" are excluded — in Chinese marine engineering
    # they describe a measurable system state, not vague intent.
]
_VAGUE_EN = [
    "as required", "as appropriate", "as needed", "if necessary",
    "sufficient", "adequate", "appropriate", "suitable", "proper",
    "reasonable", "satisfactory", "good",
    "high enough", "low enough",
    # NOTE: "stable" and "reliable" are excluded for same reason.
]

# 带单位的数值正则（检测潜在过度推理）
_UNIT_RE = re.compile(
    r"\d+\.?\d*\s*"
    r"(%|°C|℃|bar|kPa|MPa|Pa|m³/h|m3/h|L/h|l/h|L/min|l/min"
    r"|rpm|kW|MW|mm(?![a-zA-Z])|m(?![a-zA-Z])|kg(?![a-zA-Z])|t(?![a-zA-Z])|Hz|V(?![a-zA-Z])|A(?![a-zA-Z])|h(?![a-zA-Z])|min(?![a-zA-Z])|s(?![a-zA-Z]))",
    re.IGNORECASE,
)

# SysML Requirement block 必填字段（JSON key → 可读名称）
_SYSML_REQUIRED: dict[str, str] = {
    "id":                  "id (SysML Requirement::id)",
    "topic":               "name (SysML Requirement::name)",
    "shall_statement":     "text (SysML Requirement::text)",
    "verification_method": "verificationMethod",
    "evidence_ids":        "traceLinks (evidenceIds)",
}

_AMBIGUITY_PROMPT = """\
You are a requirements engineering quality checker for marine main engine cooling water systems.

Determine whether the following engineering requirement statement contains vague qualitative \
terms WITHOUT specific quantification that would make it unverifiable.

Domain context: terms like "稳定运行" (stable operation), "可靠" (reliable), "高温报警" \
(high temperature alarm) are acceptable engineering language in this domain when accompanied \
by acceptance criteria referencing measurable conditions or manufacturer data.

Flag as vague ONLY if the term is the sole basis for acceptance with no quantitative reference \
or document reference — e.g. "系统应保持稳定" (no criteria), "应满足要求" (no source specified).

Requirement:
{shall}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "ambiguous": true or false,
  "vague_terms": ["term1", "term2"],
  "suggestion": "one-line fix suggestion (empty string if not ambiguous)"
}}
"""

# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class QualityCheckResult:
    dimension: str
    passed: bool
    severity: str       # "error" | "warning"
    message: str
    suggestion: str


@dataclass
class QualityReport:
    requirement_id: str
    overall_passed: bool   # error 级全部通过才为 True；warning 不影响
    score: float           # 通过维度数 / 5，用于论文指标
    checks: list[QualityCheckResult] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "overall_passed": self.overall_passed,
            "score": self.score,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "checks": [
                {
                    "dimension": c.dimension,
                    "passed": c.passed,
                    "severity": c.severity,
                    "message": c.message,
                    "suggestion": c.suggestion,
                }
                for c in self.checks
            ],
        }


# ─────────────────────────────────────────────
# 质量门主类
# ─────────────────────────────────────────────

class QualityGate:
    """
    对单条工程需求（engineering_requirement_agent 输出的 JSON 对象）执行 5 维质量检查。

    维度及策略：
      1. evidence_sufficiency  — 规则
      2. verifiability         — 规则
      3. over_inference        — 规则
      4. ambiguity             — LLM（DeepSeek），降级为规则
      5. mbse_completeness     — 规则
    """

    def __init__(self) -> None:
        self._cfg = get_config()

    # ── 公共接口 ──────────────────────────────

    def check(self, req: dict[str, Any]) -> QualityReport:
        """检查单条需求，返回 QualityReport。"""
        checks = [
            self._evidence_sufficiency(req),
            self._verifiability(req),
            self._over_inference(req),
            self._ambiguity(req),
            self._mbse_completeness(req),
        ]
        passed_count = sum(1 for c in checks if c.passed)
        overall_passed = all(c.passed for c in checks if c.severity == "error")
        return QualityReport(
            requirement_id=safe_text(req.get("id")),
            overall_passed=overall_passed,
            score=round(passed_count / len(checks), 2),
            checks=checks,
        )

    def check_set(self, requirements: list[dict[str, Any]]) -> list[QualityReport]:
        """批量检查，返回与输入等长的 QualityReport 列表。"""
        return [self.check(req) for req in requirements]

    # ── 维度 1：证据充分性 ──────────────────────

    def _evidence_sufficiency(self, req: dict[str, Any]) -> QualityCheckResult:
        ids = req.get("evidence_ids") or []
        status = safe_text(req.get("support_status"))

        if not ids:
            return QualityCheckResult(
                dimension="evidence_sufficiency",
                passed=False,
                severity="error",
                message="evidence_ids is empty — requirement has no evidence backing.",
                suggestion="Retrieve and link at least one supporting evidence item from the evidence database.",
            )
        if status == "evidence_gap":
            return QualityCheckResult(
                dimension="evidence_sufficiency",
                passed=False,
                severity="error",
                message=f"support_status='evidence_gap' with {len(ids)} evidence ID(s) listed.",
                suggestion="Supplement the evidence database with relevant standards, manuals, or technical data.",
            )
        return QualityCheckResult(
            dimension="evidence_sufficiency",
            passed=True,
            severity="error",
            message=f"Evidence present: {len(ids)} item(s), support_status='{status}'.",
            suggestion="",
        )

    # ── 维度 2：可验证性 ────────────────────────

    def _verifiability(self, req: dict[str, Any]) -> QualityCheckResult:
        method = safe_text(req.get("verification_method"))
        criteria: list[str] = req.get("acceptance_criteria") or []

        if not method:
            return QualityCheckResult(
                dimension="verifiability",
                passed=False,
                severity="error",
                message="verification_method is missing.",
                suggestion=(
                    "Choose one of: review, inspection, calculation, test, "
                    "commissioning_check, operation_check, maintenance_check, class_approval."
                ),
            )
        if not criteria:
            return QualityCheckResult(
                dimension="verifiability",
                passed=False,
                severity="error",
                message="acceptance_criteria is empty.",
                suggestion="Define at least one measurable acceptance criterion.",
            )

        # Skip the standard evidence-gap placeholder from vague-term scanning
        real_criteria = [
            c for c in criteria
            if "待补充" not in c and "to be confirmed" not in c.lower()
        ]
        blob = " ".join(real_criteria).lower()
        hits = [w for w in _VAGUE_ZH + _VAGUE_EN if w.lower() in blob]
        if hits:
            return QualityCheckResult(
                dimension="verifiability",
                passed=False,
                severity="warning",
                message=f"Acceptance criteria contain vague placeholder(s): {hits}.",
                suggestion=(
                    "Replace vague terms with measurable conditions or explicit references "
                    "to project documents (e.g., 'per commissioning procedure Doc-XXX')."
                ),
            )
        return QualityCheckResult(
            dimension="verifiability",
            passed=True,
            severity="error",
            message=f"Verifiable: method='{method}', {len(criteria)} criterion/criteria defined.",
            suggestion="",
        )

    # ── 维度 3：过度推理（数值幻觉）──────────────

    def _over_inference(self, req: dict[str, Any]) -> QualityCheckResult:
        shall = safe_text(req.get("shall_statement"))
        status = safe_text(req.get("support_status"))
        matches = _UNIT_RE.findall(shall)

        if matches and status != "verified_by_direct_evidence":
            return QualityCheckResult(
                dimension="over_inference",
                passed=False,
                severity="error",
                message=(
                    f"Specific quantitative value(s) {matches} found in shall_statement "
                    f"but support_status='{status}' (not verified by direct evidence)."
                ),
                suggestion=(
                    "Remove specific values or replace with a placeholder referencing the source "
                    "(e.g., 'per Manufacturer Technical Data'). "
                    "Only values explicitly stated in direct evidence may appear here."
                ),
            )
        return QualityCheckResult(
            dimension="over_inference",
            passed=True,
            severity="error",
            message=(
                "No over-inference detected."
                if not matches
                else f"Value(s) {matches} present and backed by direct evidence."
            ),
            suggestion="",
        )

    # ── 维度 4：歧义性（LLM，降级规则）────────────

    def _ambiguity(self, req: dict[str, Any]) -> QualityCheckResult:
        shall = safe_text(req.get("shall_statement"))
        if self._cfg.deepseek.enabled:
            return self._ambiguity_llm(shall)
        return self._ambiguity_rule(shall)

    def _ambiguity_llm(self, shall: str) -> QualityCheckResult:
        try:
            client = OpenAI(
                api_key=self._cfg.deepseek.api_key,
                base_url=self._cfg.deepseek.base_url,
            )
            resp = client.chat.completions.create(
                model=self._cfg.deepseek.model,
                messages=[{
                    "role": "user",
                    "content": _AMBIGUITY_PROMPT.format(shall=shall),
                }],
                temperature=0.0,
                max_tokens=256,
                response_format={"type": "json_object"},
            )
            obj = json.loads(resp.choices[0].message.content or "{}")
            if obj.get("ambiguous"):
                terms = obj.get("vague_terms", [])
                return QualityCheckResult(
                    dimension="ambiguity",
                    passed=False,
                    severity="warning",
                    message=f"Ambiguous qualitative term(s) detected (LLM): {terms}.",
                    suggestion=safe_text(obj.get("suggestion")) or "Quantify or constrain the vague terms.",
                )
            return QualityCheckResult(
                dimension="ambiguity",
                passed=True,
                severity="warning",
                message="No ambiguous terms detected (LLM check).",
                suggestion="",
            )
        except Exception as exc:
            return self._ambiguity_rule(shall, note=f"LLM check failed ({exc}), using rule fallback.")

    def _ambiguity_rule(self, shall: str, note: str = "") -> QualityCheckResult:
        shall_lower = shall.lower()
        hits = [w for w in _VAGUE_ZH + _VAGUE_EN if w.lower() in shall_lower]
        prefix = f"[Rule fallback{': ' + note if note else ''}] " if note else ""
        if hits:
            return QualityCheckResult(
                dimension="ambiguity",
                passed=False,
                severity="warning",
                message=f"{prefix}Potentially ambiguous term(s): {hits}.",
                suggestion="Quantify or add specific conditions to replace vague qualitative terms.",
            )
        return QualityCheckResult(
            dimension="ambiguity",
            passed=True,
            severity="warning",
            message=f"{prefix}No ambiguous terms detected (rule check).",
            suggestion="",
        )

    # ── 维度 5：MBSE 字段完整性 ─────────────────

    def _mbse_completeness(self, req: dict[str, Any]) -> QualityCheckResult:
        missing = [
            display
            for key, display in _SYSML_REQUIRED.items()
            if not req.get(key) or (isinstance(req.get(key), list) and not req[key])
        ]
        if missing:
            return QualityCheckResult(
                dimension="mbse_completeness",
                passed=False,
                severity="error",
                message=f"Missing SysML required field(s): {missing}.",
                suggestion="Populate all SysML Requirement block fields before XML export.",
            )
        return QualityCheckResult(
            dimension="mbse_completeness",
            passed=True,
            severity="error",
            message=f"All {len(_SYSML_REQUIRED)} SysML required fields are present.",
            suggestion="",
        )
