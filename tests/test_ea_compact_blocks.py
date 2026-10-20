"""图块格式对齐 EA 原生需求图（XML/XML_of_EA/reqFig.xml、论文 fig5）：

- 图块显示 «requirement» + 名称 + tags 隔间（id = ORxxx / text = <memo> 两行），
  即元素样式 Tag=1 ——完整正文仍放在 text 属性里（memo 类型只显示 <memo>）。
- id/text tagged value 必须用 EA 的属性类型 GUID 前缀，否则 EA 导入时不识别为
  SysML 内置 id/text，会把整段正文当普通 tagged value 画在图块上（之前图块
  被撑大的根因）。前缀见 reqFig.xml：id=EAID_00000DED_3AF1_773a_，
  text=EAID_00415985_D789_37d7_。
- 图块是窄栏：原生宽 110、高随内容 160-223（RzO=1 自动适配）。
"""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ea", Path("scripts/92_export_ea_native_xmi.py"))
ea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ea)


def test_diagram_element_shows_tags_compartment_like_ea_native():
    style = ea.DIAG_ELEM_STYLE
    assert "Tag=1" in style          # tags 隔间可见（id / text = <memo> 两行）
    assert "RzO=1" in style          # 与原生一致，高度自适应内容
    assert "Tag=0" not in style


def test_blocks_are_narrow_columns_like_ea_native():
    """原生图块宽 110（名称在窄栏内自动换行），不是 300 宽的大扁框。"""
    assert ea.BOX_W <= 120
    assert ea.BOX_H <= 200


def test_id_and_text_use_ea_native_property_guid_stems():
    """id/text 的 xmi.id 前三段必须是 EA 属性类型 GUID，否则 text 不识别为 memo。"""
    id_tv = ea.req_id_value("OR041", "EAID_RID_EXAMPLE")
    text_tv = ea.req_text_value("shall text", "EAID_RID_EXAMPLE")
    assert 'tag="id"' in id_tv
    assert 'value="OR041"' in id_tv
    assert 'modelElement="EAID_RID_EXAMPLE"' in id_tv
    assert 'xmi.id="EAID_00000DED_3AF1_773a_' in id_tv
    assert 'xmi.id="EAID_00415985_D789_37d7_' in text_tv


def test_full_content_still_exported_in_text_property():
    notes = ea.er_notes(
        "The LT water ahead of the 2nd-stage charge-air cooler shall be 32 °C",
        "32 °C at 100 % load", "B", "Test", "E-SW-DRAW-002",
        derivation="Direct", route="ENGINEER_CONFIRM",
        route_reason="cites manufacturer/operational guidance only (tier-b)",
    )
    text_value = ea.req_text_value(notes, "EAID_RID_EXAMPLE")
    assert 'tag="text"' in text_value
    assert "&lt;memo&gt;#NOTES#" in text_value   # memo 前缀：图上只显示 <memo>
    assert "32" in text_value
    assert "Grade: B" in text_value
    assert "Route: ENGINEER_CONFIRM" in text_value
    assert 'modelElement=' in text_value
