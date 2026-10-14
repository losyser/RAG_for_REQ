# tests/test_paper_numbers.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("pn", Path("scripts/100_paper_numbers.py"))
pn = importlib.util.module_from_spec(spec); spec.loader.exec_module(pn)


def test_wilson_zero_n():
    assert pn.wilson(0, 0) == (None, None)


def test_wilson_zero_k_upper_bound():
    lo, hi = pn.wilson(0, 286)
    assert lo == 0.0 and 1.2 <= hi <= 1.4


def test_grade_summary_handles_empty_arm():
    s = pn.grade_summary({"result_sets": []}, kb={})
    assert s["n_shalls"] == 0 and s["grade_X_pct"] is None
