import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("lk", Path("scripts/102_leakage_check.py"))
lk = importlib.util.module_from_spec(spec); spec.loader.exec_module(lk)


def test_lcs_against_blob():
    blob = "冷却水泵应一用一备\x00膨胀水箱液位低报警"
    assert lk.lcs_len("主机冷却水泵要可靠", blob) == 4   # 冷却水泵
    assert lk.lcs_len("膨胀水箱", blob) == 4
    assert lk.lcs_len("xyz", blob) == 0


def test_lcs_does_not_cross_unit_boundary():
    blob = "abc\x00def"
    assert lk.lcs_len("cd", blob) == 1

