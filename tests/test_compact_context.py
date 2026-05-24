# tests/test_compact_context.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_context(sub_requirements):
    return {
        "requirement_id": "R001",
        "stakeholder": "船东",
        "raw_requirement_text": "系统应保证稳定可靠的冷却能力。",
        "sub_requirements": sub_requirements,
    }


def test_allowed_aspects_extracted_from_sub_requirements():
    from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context

    subs = [
        {
            "requirement_type": "redundancy",
            "topic": "冷却水泵冗余配置",
            "text": "系统应配置冗余泵。",
            "source_phrase": "稳定可靠的冷却能力",
            "implication_type": "direct_implication",
            "selected_results": [],
        },
        {
            "requirement_type": "parameter",
            "topic": "温度控制范围",
            "text": "温度应满足厂家要求。",
            "source_phrase": "温度",
            "implication_type": "explicit",
            "selected_results": [],
        },
    ]
    ctx = compact_requirement_context(_make_context(subs))

    aspects = ctx["allowed_engineering_aspects"]
    assert len(aspects) == 2
    assert aspects[0]["topic"] == "冷却水泵冗余配置"
    assert aspects[0]["source_phrase"] == "稳定可靠的冷却能力"
    assert aspects[0]["implication_type"] == "direct_implication"
    assert aspects[1]["topic"] == "温度控制范围"


def test_aspects_without_source_phrase_excluded():
    """fallback 产生的无溯源方面不应出现在 allowed_engineering_aspects 中。"""
    from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context

    subs = [
        {
            "requirement_type": "operation",
            "topic": "工况适应性",
            "text": "系统应适应各工况。",
            "source_phrase": "",          # fallback — no traceability
            "implication_type": "",
            "selected_results": [],
        },
    ]
    ctx = compact_requirement_context(_make_context(subs))
    assert ctx["allowed_engineering_aspects"] == []
