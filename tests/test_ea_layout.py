import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ea", Path("scripts/92_export_ea_native_xmi.py"))
ea = importlib.util.module_from_spec(spec); spec.loader.exec_module(ea)

BW, GX, GY = 300, 350, 320


def test_unlimited_per_row_matches_previous_single_row_layout():
    (px, py), kids, h = ea.group_layout(3, per_row=0, y_top=30, bw=BW, gapx=GX, gapy=GY)
    assert (px, py) == (40 + 3 * GX // 2 - BW // 2, 30)
    assert kids == [(40, 30 + GY), (40 + GX, 30 + GY), (40 + 2 * GX, 30 + GY)]
    assert h == 2 * GY


def test_wraps_children_into_rows_of_four():
    (px, py), kids, h = ea.group_layout(8, per_row=4, y_top=30, bw=BW, gapx=GX, gapy=GY)
    assert px == 40 + 4 * GX // 2 - BW // 2
    assert kids[3] == (40 + 3 * GX, 30 + GY)
    assert kids[4] == (40, 30 + 2 * GY)
    assert h == 3 * GY


def test_zero_children():
    (px, py), kids, h = ea.group_layout(0, per_row=4, y_top=30, bw=BW, gapx=GX, gapy=GY)
    assert kids == [] and h == GY
