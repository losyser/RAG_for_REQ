# tests/test_numeric_norm.py
from cooling_rag_mg.numeric_norm import extract_numbers


def test_ranges_and_fullwidth():
    assert extract_numbers("70–85°C") == ["70", "85"]
    assert extract_numbers("７０-８５ ℃") == ["70", "85"]


def test_decimal_and_multiplier():
    assert extract_numbers("1.5倍设计压力") == ["1.5"]
    assert extract_numbers("1.50×p") == ["1.5"]
    assert extract_numbers("≤ 2 s") == ["2"]


def test_no_numbers():
    assert extract_numbers("{{TBD|unit:°C}}") == []


def test_number_after_chinese_char():
    assert extract_numbers("当冷却水温度高于85°C时") == ["85"]
