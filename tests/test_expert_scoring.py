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


def test_stage3_prf_by_tier_skips_blank_rows():
    rows = [{"tier": "L1", "n_extracted": 4, "n_correct": 3, "n_missed": 1},
            {"tier": "L2", "n_extracted": 2, "n_correct": 2, "n_missed": 0},
            {"tier": "L2", "n_extracted": 1, "n_correct": None, "n_missed": None}]
    r = sc.stage3_prf(rows)
    assert r["ALL"]["n_units"] == 2 and r["n_skipped"] == 1
    assert r["ALL"]["precision"] == round(5 / 6 * 100, 1)
    assert r["ALL"]["recall"] == round(5 / 6 * 100, 1)
    assert r["L1"]["recall"] == 75.0
