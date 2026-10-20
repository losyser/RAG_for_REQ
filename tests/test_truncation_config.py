import importlib


def test_generator_limits_default_and_env(monkeypatch):
    import cooling_rag_mg.structured_req_generator as sg
    monkeypatch.delenv("RAG_EU_TEXT_LIMIT", raising=False)
    monkeypatch.delenv("RAG_MAX_EVIDENCE_ITEMS", raising=False)
    sg = importlib.reload(sg)
    assert (sg._EU_TEXT_LIMIT, sg._MAX_EVIDENCE_ITEMS) == (500, 12)
    monkeypatch.setenv("RAG_EU_TEXT_LIMIT", "1200")
    monkeypatch.setenv("RAG_MAX_EVIDENCE_ITEMS", "20")
    sg = importlib.reload(sg)
    assert (sg._EU_TEXT_LIMIT, sg._MAX_EVIDENCE_ITEMS) == (1200, 20)
    monkeypatch.delenv("RAG_EU_TEXT_LIMIT"); monkeypatch.delenv("RAG_MAX_EVIDENCE_ITEMS")
    importlib.reload(sg)


class _Msg:
    content = '{"values": []}'


class _Resp:
    choices = [type("C", (), {"message": _Msg()})()]


class _Client:
    def __init__(self):
        self.prompts = []
        self.chat = type("Ch", (), {"completions": self})()
    def create(self, **kw):
        self.prompts.append(kw["messages"][0]["content"])
        return _Resp()


def test_extractor_char_limit_env(monkeypatch):
    from cooling_rag_mg.kb_value_extractor import extract_values_from_evidence
    c = _Client()
    monkeypatch.delenv("RAG_EXTRACT_CHAR_LIMIT", raising=False)
    extract_values_from_evidence("a" * 1000 + "\n\n" + "b" * 1000 + "\n\n" + "c" * 1000, c, "m")
    monkeypatch.setenv("RAG_EXTRACT_CHAR_LIMIT", "2400")
    extract_values_from_evidence("a" * 1000 + "\n\n" + "b" * 1000 + "\n\n" + "c" * 1000, c, "m")
    assert "a" * 1000 in c.prompts[0]
    assert "b" * 1000 not in c.prompts[0]
    assert "b" * 1000 in c.prompts[1]
    assert "c" * 1000 not in c.prompts[1]
