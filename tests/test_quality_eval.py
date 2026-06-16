from unittest.mock import MagicMock

from cooling_rag_mg.quality_eval import (
    aggregate_quality, consensus_pair, numeric_fraction, traceability_rate,
)


def _resp(c):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="qwen")


def test_consensus_agrees_keeps_verdict():
    # 两次盲评（左右交换）都判 R 更好的维度 → 共识 R；位置偏置 False
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"completeness":"A","actionability":"A","consistency":"A","verifiability":"A"}'),  # R 在左
        _resp('{"completeness":"B","actionability":"B","consistency":"B","verifiability":"B"}'),  # R 在右
    ]
    cons, biased = consensus_pair("原始", r_text="R", b0_text="B0", client=client, model="qwen")
    assert cons["completeness"] == "R"
    assert cons["actionability"] == "R"
    assert biased["completeness"] is False


def test_consensus_disagreement_becomes_tie_and_flags_bias():
    client = MagicMock()
    # 第一次 R(左)判 A=R更好；第二次 R(右)判 A=R更差 → 两次都偏左 → 位置偏置 → tie
    client.chat.completions.create.side_effect = [
        _resp('{"completeness":"A","actionability":"tie","consistency":"tie","verifiability":"tie"}'),
        _resp('{"completeness":"A","actionability":"tie","consistency":"tie","verifiability":"tie"}'),
    ]
    cons, biased = consensus_pair("原始", r_text="R", b0_text="B0", client=client, model="qwen")
    assert cons["completeness"] == "tie"
    assert biased["completeness"] is True


def test_aggregate_quality_counts_and_winrate():
    rows = [
        {"completeness": "R", "actionability": "B0", "consistency": "tie", "verifiability": "R"},
        {"completeness": "R", "actionability": "R",  "consistency": "B0", "verifiability": "tie"},
    ]
    agg = aggregate_quality(rows)
    assert agg["completeness"] == {"R": 2, "B0": 0, "tie": 0}
    assert agg["actionability"] == {"R": 1, "B0": 1, "tie": 0}
    # 总体 R 胜率（4 dims × 2 rows = 8 total）
    assert agg["overall"]["R"] == 4 and agg["overall"]["B0"] == 2 and agg["overall"]["tie"] == 2


def test_numeric_fraction():
    ers = [{"shall_statement": "液位低于20%报警"}, {"shall_statement": "应设置报警装置"}]
    assert numeric_fraction(ers) == 0.5


def test_traceability_rate():
    ers = [{"shall_statement": "x", "evidence_ids": ["e1"]},
           {"shall_statement": "y", "evidence_ids": []},
           {"shall_statement": "z"}]
    assert abs(traceability_rate(ers) - 1 / 3) < 1e-9
