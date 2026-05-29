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


def test_load_evidence_text_map(tmp_path):
    from cooling_rag_mg.jsonl import write_jsonl
    from cooling_rag_mg.grounding import load_evidence_text_map
    p = tmp_path / "units.jsonl"
    write_jsonl(p, [
        {"id": "E-A-001", "text": "海水泵应一用一备。"},
        {"id": "E-A-002", "text": "冷却水高温报警阈值见厂家数据。"},
    ])
    m = load_evidence_text_map(p)
    assert m["E-A-001"] == "海水泵应一用一备。"
    assert m["E-A-002"].startswith("冷却水高温报警")
    assert "E-MISSING" not in m


def test_iter_grounded_ers():
    from cooling_rag_mg.grounding import iter_grounded_ers
    result_sets = [{
        "source_requirement_id": "P001",
        "engineering_requirements": [
            {"shall_statement": "应一用一备。", "evidence_ids": ["E-A-001"]},
            {"shall_statement": "无证据条目。", "evidence_ids": []},
            {"shall_statement": "", "evidence_ids": ["E-A-002"]},  # 空 shall 跳过
        ],
    }]
    out = list(iter_grounded_ers(result_sets))
    assert out == [("P001", "应一用一备。", ["E-A-001"])]
