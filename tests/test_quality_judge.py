from unittest.mock import MagicMock


def _resp(c):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="qwen")


def test_parse_pairwise():
    from cooling_rag_mg.quality_judge import parse_pairwise
    raw = '{"completeness":"A","actionability":"B","consistency":"tie","verifiability":"A"}'
    d = parse_pairwise(raw)
    assert d == {"completeness": "A", "actionability": "B", "consistency": "tie", "verifiability": "A"}


def test_parse_pairwise_normalizes_illegal_to_tie():
    from cooling_rag_mg.quality_judge import parse_pairwise
    d = parse_pairwise('{"completeness":"maybe"}')
    assert d["completeness"] == "tie" and d["verifiability"] == "tie"


def test_judge_pair_normalizes_to_target_when_R_is_A():
    from cooling_rag_mg.quality_judge import judge_pair
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"completeness":"A","actionability":"tie","consistency":"B","verifiability":"A"}')
    ]
    res = judge_pair("原始需求", r_text="R内容", b0_text="B0内容", r_on_left=True, client=client, model="qwen")
    assert res["completeness"] == "R" and res["consistency"] == "B0" and res["actionability"] == "tie"


def test_judge_pair_normalizes_when_R_is_B():
    from cooling_rag_mg.quality_judge import judge_pair
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"completeness":"A","actionability":"B","consistency":"tie","verifiability":"B"}')
    ]
    res = judge_pair("原始需求", r_text="R内容", b0_text="B0内容", r_on_left=False, client=client, model="qwen")
    assert res["completeness"] == "B0" and res["verifiability"] == "R" and res["consistency"] == "tie"
