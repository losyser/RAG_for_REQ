import os
from cooling_rag_mg.config import get_config


def test_qwen_ernie_config_present(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "sk-qwen-test")
    monkeypatch.setenv("ERNIE_API_KEY", "bce-ernie-test")
    cfg = get_config()
    assert cfg.qwen.api_key == "sk-qwen-test"
    assert cfg.qwen.model == "qwen-max"
    assert cfg.qwen.base_url.endswith("/compatible-mode/v1")
    assert cfg.qwen.enabled is True
    assert cfg.ernie.api_key == "bce-ernie-test"
    assert cfg.ernie.base_url.endswith("qianfan.baidubce.com/v2")
    assert cfg.ernie.enabled is True
