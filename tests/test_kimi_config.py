def test_kimi_config(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "sk-kimi-test")
    from cooling_rag_mg.config import get_config
    cfg = get_config()
    assert cfg.kimi.api_key == "sk-kimi-test"
    assert cfg.kimi.base_url.endswith("moonshot.cn/v1")
    assert cfg.kimi.model.startswith("moonshot")
    assert cfg.kimi.enabled is True
