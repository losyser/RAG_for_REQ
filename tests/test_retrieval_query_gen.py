from unittest.mock import MagicMock


def _resp(c):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="kimi")


def test_build_query_prompt_asks_zh_en_keywords_sentences():
    from cooling_rag_mg.retrieval_query_gen import build_query_prompt
    p = build_query_prompt("海水泵应一用一备")
    assert "关键词" in p and ("英文" in p or "English" in p) and "海水泵应一用一备" in p


def test_parse_queries_flattens_keywords_and_sentences():
    from cooling_rag_mg.retrieval_query_gen import parse_queries
    raw = '{"keywords":["海水泵","seawater pump"],"sentences":["海水泵应冗余","seawater pump shall be redundant"]}'
    qs = parse_queries(raw)
    assert "海水泵" in qs and "seawater pump shall be redundant" in qs
    assert len(qs) == 4 and len(set(qs)) == 4


def test_parse_queries_empty_on_failure():
    from cooling_rag_mg.retrieval_query_gen import parse_queries
    assert parse_queries("not json") == []


def test_generate_queries_calls_kimi():
    from cooling_rag_mg.retrieval_query_gen import generate_queries
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"keywords":["海水泵"],"sentences":["seawater pump redundancy"]}')
    ]
    qs = generate_queries("海水泵应一用一备", client, model="kimi")
    assert qs == ["海水泵", "seawater pump redundancy"]
