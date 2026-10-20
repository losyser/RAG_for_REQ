# Regression: deepseek-flash outputs for evidence-rich requirements exceeded max_tokens=4000,
# were truncated (finish_reason="length"), failed JSON parsing and yielded zero shalls.
from cooling_rag_mg.structured_req_generator import generate_norag_shalls, generate_structured_shalls


class _Client:
    def __init__(self):
        self.kw = None
        self.chat = type("Ch", (), {"completions": self})()
    def create(self, **kw):
        self.kw = kw
        msg = type("M", (), {"content": '{"shalls": []}'})()
        return type("R", (), {"choices": [type("C", (), {"message": msg, "finish_reason": "stop"})()]})()


def test_structured_generation_default_token_limit_is_8192():
    c = _Client()
    generate_structured_shalls("req", [{"id": "E1", "text": "t", "_extracted_values": []}], c, "m")
    assert c.kw["max_tokens"] == 8192


def test_norag_generation_default_token_limit_is_8192():
    c = _Client()
    generate_norag_shalls("req", c, "m")
    assert c.kw["max_tokens"] == 8192


def test_selection_default_token_limit_is_8192(monkeypatch):
    import cooling_rag_mg.llm_cache as lc
    import cooling_rag_mg.req_generation_v2 as rg
    seen = {}
    def fake(client, *, model, messages, temperature, max_tokens, response_format=None, force=False):
        seen["max_tokens"] = max_tokens
        msg = type("M", (), {"content": '{"engineering_requirements": []}'})()
        return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()
    monkeypatch.setattr(lc, "cached_completion", fake)
    rg.generate_rag_v3("req", [{"id": "E1", "text": "t"}], None, "m", temperature=0.0)
    assert seen["max_tokens"] == 8192
