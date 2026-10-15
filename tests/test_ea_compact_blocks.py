"""图上的需求框只显示 «requirement» + 名称：完整内容必须放进 EA 的 text
属性（打开元素可见），不能显示在图块上，否则框被撑大、价值密度低。"""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ea", Path("scripts/92_export_ea_native_xmi.py"))
ea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ea)


def test_diagram_element_hides_tagged_value_compartment():
    style = ea.DIAG_ELEM_STYLE
    assert "Tag=0" in style
    assert "Tag=1" not in style


def test_blocks_are_compact_since_text_is_hidden():
    """只显示名称，框高必须明显收窄（不再为整段 text 预留 200px）。"""
    assert ea.BOX_H <= 100
    assert ea.BOX_W <= 300


def test_full_content_still_exported_in_text_property():
    notes = ea.er_notes(
        "The LT water ahead of the 2nd-stage charge-air cooler shall be 32 °C",
        "32 °C at 100 % load", "B", "Test", "E-SW-DRAW-002",
        derivation="Direct", route="ENGINEER_CONFIRM",
        route_reason="cites manufacturer/operational guidance only (tier-b)",
    )
    text_value = ea.req_text_value(notes, "EAID_RID_EXAMPLE")
    assert 'tag="text"' in text_value
    assert "32" in text_value
    assert "Grade: B" in text_value
    assert "Route: ENGINEER_CONFIRM" in text_value
    assert 'modelElement=' in text_value
