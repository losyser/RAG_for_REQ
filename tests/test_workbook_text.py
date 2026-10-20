import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("wb", Path("scripts/97_build_expert_workbook.py"))
wb = importlib.util.module_from_spec(spec); spec.loader.exec_module(wb)


def test_annotator_text_strips_curator_notes_with_labels():
    t = "冷却液防腐剂\n9.1.1 Corrosion inhibitors are mandatory.\n整理说明：原文涉及…\n可支撑：coolant 的 water_quality\n不能支撑：1. …"
    out = wb.annotator_text(t)
    assert "water_quality" not in out and "整理说明" not in out and "可支撑" not in out
    assert "Corrosion inhibitors are mandatory." in out


def test_annotator_text_strips_inline_applicability_label_note():
    t = "冷却水连接关系：中间管 13016 数量 8。适用条件：根据 spare parts，针对 pipe 的 arrangement 方面提供原文依据。\n\n可支撑：冷却水系统布置"
    out = wb.annotator_text(t)
    assert "可支撑" not in out and "arrangement 方面" not in out
