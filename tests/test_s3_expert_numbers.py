import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("s3n", ROOT / "scripts/113_s3_expert_numbers.py")
s3n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s3n)


@pytest.fixture(scope="module")
def res():
    if not s3n.RES.exists():
        pytest.skip("S3 review result not present")
    return json.loads(s3n.RES.read_text(encoding="utf-8"))


def test_counts_cover_all_items(res):
    m = s3n.numbers(res)
    for tag in ("Rag", "NoRag"):
        assert sum(m[f"SThree{tag}{k}"] for k in ("Correct", "Acceptable", "Wrong", "Unknown")) == m[f"SThree{tag}N"] == 25
        assert sum(m[f"SThree{tag}{k}"] for k in ("Appl", "NotAppl", "CondUnknown")) == 25


def test_error_causes_match_rag_wrong(res):
    m = s3n.numbers(res)
    assert m["SThreeErrTable"] + m["SThreeErrBinding"] + m["SThreeErrGen"] == m["SThreeRagWrong"]


def test_primary_difference_consistent(res):
    m = s3n.numbers(res)
    assert m["SThreeDiff"] == pytest.approx(m["SThreeRagSrcRate"] - m["SThreeNoRagSrcRate"])
    assert m["SThreeBoundLo"] <= m["SThreeDiff"] <= m["SThreeBoundHi"]
    assert m["SThreeSignPos"] + m["SThreeSignNeg"] + m["SThreeSignTies"] == m["SThreeSources"]


def test_fmt_signs_and_rounding():
    assert s3n.fmt("SThreeBootLo", 0.125) == "0.13"
    assert s3n.fmt("SThreeBoundLo", -0.5) == r"\ensuremath{-0.50}"
    assert s3n.fmt("SThreeDiff", 0.3) == r"\ensuremath{+0.30}"
    assert s3n.fmt("SThreeRagN", 25) == "25"
