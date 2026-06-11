import json
from unittest.mock import MagicMock


def _resp(content):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


_SAMPLE_SHALLS = json.dumps([
    {
        "shall_statement": "冷却水泵出口压力应满足要求",
        "measurable_criterion": "{{TBD|unit:MPa|ref:MAN-SL2014-584|component:cooling_water_pump|intent:pressure|hint:额定转速下出口压力}}",
        "applicable_condition": "额定转速正常工况",
        "verification_method": "海试实测",
        "acceptance_criteria": ["压力传感器读数满足要求"],
        "evidence_citations": [{"kb_id": "EU-001", "tier": "L2", "source": "MAN-SL2014-584", "has_clause": False}],
    }
], ensure_ascii=False)


def test_generate_structured_shalls_returns_list():
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"shalls": ' + _SAMPLE_SHALLS + '}')
    result = generate_structured_shalls(
        source_requirement="冷却水泵应提供足够压力",
        annotated_evidence=[{
            "id": "EU-001", "kb_tier": "L2", "source_document": "MAN-SL2014-584",
            "text": "冷却水泵出口压力参考值见厂家数据表",
            "_extracted_values": [], "_has_quantitative": False,
        }],
        client=client,
        model="m",
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert "shall_statement" in result[0]
    assert "measurable_criterion" in result[0]
    assert "evidence_citations" in result[0]


def test_generate_structured_shalls_api_error_returns_empty():
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    client = MagicMock()
    client.chat.completions.create.side_effect = Exception("timeout")
    result = generate_structured_shalls("需求", [], client, "m")
    assert result == []


def test_generate_norag_shalls_has_no_evidence_citations():
    from cooling_rag_mg.structured_req_generator import generate_norag_shalls
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"shalls": [{"shall_statement": "系统应稳定运行", "measurable_criterion": "10秒", "applicable_condition": "正常工况", "verification_method": "测试", "acceptance_criteria": ["10秒内完成"], "evidence_citations": []}]}')
    result = generate_norag_shalls("冷却系统应稳定运行", client, "m")
    assert isinstance(result, list)
    assert result[0]["evidence_citations"] == []


def test_build_evidence_block_includes_extracted_values():
    from cooling_rag_mg.structured_req_generator import _build_evidence_block
    units = [{
        "id": "EU-001", "kb_tier": "L1", "source_document": "CCS-2024",
        "text": "温度不超过 85°C",
        "_extracted_values": [{"value_text": "85°C", "operator": "<=", "unit": "°C"}],
        "_has_quantitative": True,
    }]
    block = _build_evidence_block(units)
    assert "EU-001" in block
    assert "85°C" in block
    assert "L1" in block
