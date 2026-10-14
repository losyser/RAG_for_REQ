# tests/test_expert_scoring.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("sc", Path("scripts/98_score_expert_workbook.py"))
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)


def test_kappa_skips_blank_and_invalid():
    a = ["pump", "", "cooler", "pump", "BAD"]
    b = ["pump", "pump", "cooler", "cooler", "pump"]
    r = sc.score_kappa(a, b, valid={"pump", "cooler"})
    assert r["n_used"] == 3 and r["n_skipped"] == 2


def test_prf_micro():
    pred = {"OR1": {("a", "x"), ("b", "y")}, "OR2": {("c", "z")}}
    gold = {"OR1": {("a", "x")}, "OR2": {("c", "z"), ("d", "w")}}
    r = sc.prf(pred, gold)
    assert r["precision"] == round(2 / 3 * 100, 1) and r["recall"] == round(2 / 3 * 100, 1)


def test_prf_empty_gold_no_crash():
    assert sc.prf({"OR1": set()}, {"OR1": set()})["f1"] is None
