from unittest.mock import MagicMock


def _resp(content):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


def test_extract_values_returns_list_with_value():
    from cooling_rag_mg.kb_value_extractor import extract_values_from_evidence
    client = MagicMock()
    client.chat.completions.create.return_value = _resp(
        '{"values": [{"value_text": "不超过 0.05 bar", "operator": "<=", "unit": "bar"}]}'
    )
    result = extract_values_from_evidence("压差不超过 0.05 bar", client, model="m")
    assert result == [{"value_text": "不超过 0.05 bar", "operator": "<=", "unit": "bar"}]


def test_extract_values_empty_text_returns_empty():
    from cooling_rag_mg.kb_value_extractor import extract_values_from_evidence
    client = MagicMock()
    result = extract_values_from_evidence("", client, model="m")
    assert result == []
    client.chat.completions.create.assert_not_called()


def test_extract_values_api_error_returns_empty():
    from cooling_rag_mg.kb_value_extractor import extract_values_from_evidence
    client = MagicMock()
    client.chat.completions.create.side_effect = Exception("timeout")
    result = extract_values_from_evidence("温度 85°C", client, model="m")
    assert result == []


def test_annotate_evidence_units_sets_has_quantitative():
    from cooling_rag_mg.kb_value_extractor import annotate_evidence_units
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"values": [{"value_text": "85°C", "operator": "<=", "unit": "°C"}]}'),
        _resp('{"values": []}'),
    ]
    units = [
        {"id": "EU-001", "text": "温度不超过 85°C", "kb_tier": "L1"},
        {"id": "EU-002", "text": "应满足制造商要求", "kb_tier": "L2"},
    ]
    result = annotate_evidence_units(units, client, model="m")
    assert result[0]["_has_quantitative"] is True
    assert result[0]["_extracted_values"] == [{"value_text": "85°C", "operator": "<=", "unit": "°C"}]
    assert result[1]["_has_quantitative"] is False
    assert result[1]["_extracted_values"] == []


def test_annotate_preserves_original_fields():
    from cooling_rag_mg.kb_value_extractor import annotate_evidence_units
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"values": []}')
    units = [{"id": "EU-003", "text": "x", "kb_tier": "L3", "source_document": "MAN"}]
    result = annotate_evidence_units(units, client, model="m")
    assert result[0]["source_document"] == "MAN"
    assert result[0]["id"] == "EU-003"
