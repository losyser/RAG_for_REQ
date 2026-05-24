# tests/test_scope_validation.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cooling_rag_mg.engineering_requirement_agent import normalize_agent_output


def _base_er(topic: str, er_id: str = "ER-R001-01") -> dict:
    return {
        "id": er_id,
        "parent_id": "ER-R001",
        "level": 1,
        "requirement_type": "redundancy",
        "topic": topic,
        "shall_statement": f"系统应满足{topic}要求。",
        "engineering_rationale": f"本条覆盖方面【{topic}】。",
        "acceptance_criteria": ["满足设计要求。"],
        "verification_method": "review",
        "evidence_ids": [],
        "support_status": "need_confirmation",
        "applicability_constraints": [],
        "risk_if_unmet": "",
    }


def _base_obj(ers, allowed_aspects):
    return {
        "requirement_set_id": "ER-R001",
        "source_requirement_id": "R001",
        "stakeholder": "船东",
        "allowed_engineering_aspects": allowed_aspects,
        "engineering_requirements": ers,
        "relationships": [],
        "evidence_gaps": [],
        "confirmation_items": [],
    }


def test_scope_violation_moved_to_evidence_gaps():
    """topic 不在 allowed_aspects 中的条目应移入 evidence_gaps。"""
    allowed = [{"topic": "冷却水泵冗余配置", "source_phrase": "稳定可靠", "implication_type": "direct_implication"}]
    ers = [
        _base_er("冷却水泵冗余配置", "ER-R001-01"),
        _base_er("倾斜工况适应性", "ER-R001-02"),   # out of scope
    ]
    result = normalize_agent_output(_base_obj(ers, allowed), "R001")

    remaining = [r["topic"] for r in result["engineering_requirements"]]
    assert "冷却水泵冗余配置" in remaining
    assert "倾斜工况适应性" not in remaining

    gap_types = [g["gap_type"] for g in result["evidence_gaps"]]
    assert "scope_violation" in gap_types


def test_no_allowed_aspects_skips_validation():
    """allowed_engineering_aspects 为空时不做范围校验，所有 ER 保留。"""
    ers = [_base_er("任意方面")]
    result = normalize_agent_output(_base_obj(ers, []), "R001")
    assert len(result["engineering_requirements"]) == 1


def test_all_valid_topics_preserved():
    """所有 topic 都在 allowed_aspects 中时，无条目被移除。"""
    allowed = [
        {"topic": "温度控制范围", "source_phrase": "温度", "implication_type": "explicit"},
        {"topic": "冷却水泵冗余配置", "source_phrase": "稳定可靠", "implication_type": "direct_implication"},
    ]
    ers = [
        _base_er("温度控制范围", "ER-R001-01"),
        _base_er("冷却水泵冗余配置", "ER-R001-02"),
    ]
    result = normalize_agent_output(_base_obj(ers, allowed), "R001")
    assert len(result["engineering_requirements"]) == 2
    assert result["evidence_gaps"] == []
