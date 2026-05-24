import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cooling_rag_mg.pipeline import build_sub_payload


def test_build_sub_payload_passes_source_phrase():
    sub = {
        "sub_id": "01",
        "requirement_type": "redundancy",
        "topic": "冷却水泵冗余配置",
        "text": "系统应配置冗余冷却水泵。",
        "source_phrase": "稳定可靠的冷却能力",
        "implication_type": "direct_implication",
        "split_method": "deepseek_v2",
    }
    result = build_sub_payload("R001", 1, sub)
    assert result["source_phrase"] == "稳定可靠的冷却能力"
    assert result["implication_type"] == "direct_implication"


def test_build_sub_payload_defaults_missing_fields():
    sub = {
        "sub_id": "01",
        "requirement_type": "operation",
        "topic": "工况适应性",
        "text": "系统应适应各工况。",
        "split_method": "fallback_rule",
    }
    result = build_sub_payload("R002", 1, sub)
    assert result["source_phrase"] == ""
    assert result["implication_type"] == ""
