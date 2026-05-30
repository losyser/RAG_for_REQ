from unittest.mock import MagicMock


def _resp(c):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="ds")


def test_norag_prompt_is_strong_not_polisher():
    from cooling_rag_mg.req_generation_v2 import build_norag_messages
    m = build_norag_messages("海水泵应一用一备")
    sys = m[0]["content"]
    assert "海水泵应一用一备" in m[1]["content"]
    assert "完整" in sys and "具体" in sys
    assert "润色" in sys  # 明确否定"仅润色"


def test_rag_messages_carry_evidence():
    from cooling_rag_mg.req_generation_v2 import build_rag_messages
    m = build_rag_messages("海水泵应一用一备", ["海水泵一用一备", "备用泵自动投入"])
    u = m[1]["content"]
    assert "海水泵一用一备" in u and "备用泵自动投入" in u and "证据" in u


def test_parse_and_tag_attaches_evidence_ids():
    from cooling_rag_mg.req_generation_v2 import parse_requirements
    raw = '{"engineering_requirements":[{"shall_statement":"应一用一备。"}, "坏元素"]}'
    out = parse_requirements(raw, evidence_ids=["E1"])
    assert len(out) == 1 and out[0]["shall_statement"] == "应一用一备。"
    assert out[0]["evidence_ids"] == ["E1"]


def test_parse_non_list_returns_empty():
    from cooling_rag_mg.req_generation_v2 import parse_requirements
    assert parse_requirements('{"engineering_requirements":"x"}', evidence_ids=[]) == []


def test_generate_norag_returns_list():
    from cooling_rag_mg.req_generation_v2 import generate_norag
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"engineering_requirements":[{"shall_statement":"应一用一备。"}]}')
    ]
    out = generate_norag("海水泵应一用一备", client, model="ds")
    assert out[0]["shall_statement"] == "应一用一备。" and out[0]["evidence_ids"] == []


def test_generate_rag_attaches_ids():
    from cooling_rag_mg.req_generation_v2 import generate_rag
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"engineering_requirements":[{"shall_statement":"应一用一备。"}]}')
    ]
    out = generate_rag("海水泵应一用一备", ["证据A"], ["E1", "E2"], client, model="ds")
    assert out[0]["evidence_ids"] == ["E1", "E2"]
