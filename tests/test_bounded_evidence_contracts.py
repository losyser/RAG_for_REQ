import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from cooling_rag_mg.evidence_contracts import (
    ordered_evidence_ids, select_evidence, bounded_context, bounded_value_records, validate_values,
)
from cooling_rag_mg.grade_classifier import classify_grade, classify_result_set, valid_citation_ids, CLASSIFIER_VERSION
from cooling_rag_mg.structured_req_generator import _build_evidence_block, _parse_shalls
from cooling_rag_mg.kb_value_extractor import annotate_evidence_units

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def saved():
    kb = {u["id"]: u for u in map(json.loads, (ROOT / "data/processed/evidence_units_v3_audited.jsonl").read_text(encoding="utf-8").splitlines())}
    rs = json.loads((ROOT / "data/search_results/exp_v4/rag_v4_results.json").read_text(encoding="utf-8"))["result_sets"]
    return kb, {r["source_requirement_id"]: r for r in rs}


def test_saved_three_cases_rule_changes_only(saved):
    kb, rs = saved
    for sid, pos, expected in [("OR001", 0, "C"), ("OR010", 0, "B"), ("OR023", 4, "B")]:
        original = copy.deepcopy(rs[sid])
        graded = classify_result_set(rs[sid], kb)["engineering_requirements"][pos]
        assert graded["_grade"] == expected
        assert graded["_grade_version"] == CLASSIFIER_VERSION
        assert "not_correctness" in graded["_grade_scope"]
        assert rs[sid] == original
    assert "-100°C" in rs["OR023"]["engineering_requirements"][4]["measurable_criterion"]


@pytest.mark.parametrize("criterion", ["{TBD|hint:80°C}", "{{TBD|hint:80°C}}", "｛ＴＢＤ｜hint:80℃｝", "{ tbd |hint:80°C}"])
def test_placeholder_always_precedes_numeric(criterion):
    assert classify_grade(criterion, [], {}) == "C"


def test_units_unicode_and_exact_citation_boundary():
    kb = {"L1-规则-第3.2条": {"kb_tier": "L1", "metadata": {"location": "3.2"}}}
    eid = next(iter(kb))
    assert classify_grade("≤ １０ dGH", [eid], kb) == "A"
    assert classify_grade("10 dGHsuffix", [eid], kb) == "C"
    assert classify_grade("10 m³/h", [eid], kb) == "A"
    assert valid_citation_ids(eid + "-suffix", kb) == []
    assert valid_citation_ids("prefix" + eid, kb) == []
    assert valid_citation_ids([eid, {"kb_id": eid}], kb) == [eid]


def test_first_reference_dedup_and_more_than_twelve():
    ids = ordered_evidence_ids([{"evidence_ids": ["E2", "E1", "E2"]}, {"evidence_ids": ["E0", "E1"]}])
    assert ids == ["E2", "E1", "E0"]
    values = [{"value_text": "10", "operator": "<=", "unit": "dGH"}]
    units = [{"id": f"E{i}", "_extracted_values": values if i % 2 else []} for i in range(20)]
    picked = select_evidence(units + [units[0]], 12)
    assert [e["id"] for e in picked] == [f"E{i}" for i in range(1, 20, 2)] + ["E0", "E2"]
    with pytest.raises(ValueError, match="conflicting"):
        select_evidence([units[0], {"id": "E0", "_extracted_values": values}])


def test_lossless_records_and_explicit_missing_context():
    value = {"value_text": "10", "operator": "<=", "unit": "dGH", "parameter": "hardness", "conditions": "fresh water", "model": "MAN", "source_span": "hardness <= 10 dGH"}
    text, omitted = bounded_value_records([value])
    assert json.loads(text) == value and omitted == 0
    legacy = {"value_text": "10", "operator": "<=", "unit": "dGH"}
    text, _ = bounded_value_records([legacy])
    assert json.loads(text)["conditions"] is None
    assert json.loads(text)["model"] is None
    block = _build_evidence_block([{"id": "E", "text": "hardness <= 10 dGH", "_extracted_values": [legacy]}])
    assert '"unit": "dGH"' in block and '"operator": "<="' in block
    assert '"engine_model": null' in block
    assert "未记录" in block


def test_context_and_parameter_records_are_atomic_and_bounded():
    paragraph = "Temperature 80°C\nCondition: startup only."
    text, omitted = bounded_context(paragraph + "\n\n" + "x" * 600, len(paragraph))
    assert text == paragraph and omitted == 1
    text, omitted = bounded_context(paragraph, 10)
    assert text == "" and omitted == 1
    value = {"value_text": "80", "operator": "<=", "unit": "°C", "conditions": "x" * 2000}
    text, omitted = bounded_value_records([value], 1600)
    assert text == "" and omitted == 1


@pytest.mark.parametrize("change", [
    {"measurable_criterion": 10}, {"applicable_condition": ""}, {"acceptance_criteria": "ok"},
    {"evidence_citations": [{"kb_id": "E", "tier": "L2", "source": "s", "has_clause": "yes"}]},
])
def test_invalid_shall_schema_is_rejected_not_partially_accepted(saved, change):
    _, rs = saved
    valid = copy.deepcopy(rs["OR010"]["engineering_requirements"][0])
    invalid = {**valid, **change}
    with pytest.raises(ValueError, match="invalid shall schema"):
        _parse_shalls(json.dumps({"shalls": [valid, invalid]}))


@pytest.mark.parametrize("value", [None, {"value_text": "10", "operator": "<=", "unit": 1}, {"value_text": "10", "unit": "bar"}, {"value_text": "10", "operator": "<=", "unit": "bar", "conditions": []}])
def test_bad_parameter_schema_is_rejected(value):
    with pytest.raises(ValueError):
        validate_values([value])


def test_extraction_failure_is_not_no_numeric_content():
    client = MagicMock()
    client.chat.completions.create.return_value.choices[0].message.content = '{"values": []}'
    client.chat.completions.create.return_value.choices[0].finish_reason = "stop"
    unit = {"id": "E", "text": "no numbers here"}
    assert annotate_evidence_units([unit], client, "offline")[0]["_extraction_status"] == "no_values"
    client.chat.completions.create.side_effect = RuntimeError("offline synthetic failure")
    assert annotate_evidence_units([unit], client, "offline")[0]["_extraction_status"] == "api_error"


def test_invented_source_span_rejected():
    client = MagicMock()
    client.chat.completions.create.return_value.choices[0].message.content = json.dumps({"values": [{"value_text": "10", "unit": "bar", "operator": "=", "source_span": "invented"}]})
    client.chat.completions.create.return_value.choices[0].finish_reason = "stop"
    result = annotate_evidence_units([{"id": "E", "text": "10 bar"}], client, "offline")
    assert result[0]["_extracted_values"] == []
    assert result[0]["_extraction_status"] == "schema_error"


def test_multiprocess_prompt_hash_is_seed_independent():
    code = r'''
import hashlib,json
from pathlib import Path
from cooling_rag_mg.evidence_contracts import ordered_evidence_ids
from cooling_rag_mg.structured_req_generator import _build_evidence_block, _STRUCTURED_GEN_PROMPT
root=Path.cwd()
kb={u['id']:u for u in map(json.loads,(root/'data/processed/evidence_units_v3_audited.jsonl').read_text(encoding='utf-8').splitlines())}
rs=json.loads((root/'data/search_results/exp_v4/rag_v4_results.json').read_text(encoding='utf-8'))['result_sets']
blocks=[]
for r in rs:
    vals=r.get('_evidence_values',{})
    ids=ordered_evidence_ids([{'evidence_ids':list(vals)}])
    block=_build_evidence_block([{**kb[i], '_extracted_values':vals[i]} for i in ids if i in kb])
    blocks.append(_STRUCTURED_GEN_PROMPT.format(source_requirement=r['source_requirement_id'], evidence_block=block))
print(hashlib.sha256('\n'.join(blocks).encode('utf-8')).hexdigest())
'''
    hashes = []
    for seed in ("1", "17", "123"):
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"}
        hashes.append(subprocess.check_output([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, text=True).strip())
    assert len(set(hashes)) == 1
    assert len(hashes[0]) == 64


def test_legacy_operator_words_are_preserved():
    for operator in ("最大", "up to", "max", "大于", "min."):
        value = {"value_text": "10", "operator": operator, "unit": "bar"}
        assert validate_values([value]) == [value]
        assert json.loads(bounded_value_records([value])[0])["operator"] == operator


def test_invalid_shalls_container_rejected():
    with pytest.raises(ValueError, match="shalls must be a list"):
        _parse_shalls('{"shalls": {"shall_statement": "bad container"}}')


def test_v4_entrypoint_offline_integration(tmp_path, monkeypatch):
    import runpy
    from types import SimpleNamespace
    module = runpy.run_path(str(ROOT / "scripts/77_run_v4_rag.py"), run_name="offline_test")
    main = module["main"]
    ns = main.__globals__
    v3 = tmp_path / "v3.json"
    v3.write_text(json.dumps({"result_sets": [{"source_requirement_id": "OR-test", "engineering_requirements": [{"evidence_ids": ["E-test", "E-test"]}]}]}), encoding="utf-8")
    kb = tmp_path / "kb.jsonl"
    kb.write_text(json.dumps({"id": "E-test", "kb_tier": "L2", "source_document": "offline fixture", "text": "Hardness <= 10 dGH for fresh water.", "metadata": {"applicable_condition": "fresh water"}}), encoding="utf-8")
    sources = tmp_path / "sources.jsonl"
    sources.write_text(json.dumps({"requirement_id": "OR-test", "requirement_text": "water quality"}), encoding="utf-8")
    shall = {"shall_statement": "Hardness shall meet the limit", "measurable_criterion": "<= 10 dGH", "applicable_condition": "fresh water", "verification_method": "test", "acceptance_criteria": ["<= 10 dGH"], "evidence_citations": [{"kb_id": "E-test", "tier": "L2", "source": "offline fixture", "has_clause": False}]}
    payloads = [json.dumps({"values": [{"value_text": "10", "operator": "<=", "unit": "dGH", "conditions": "fresh water", "source_span": "Hardness <= 10 dGH for fresh water."}]}), json.dumps({"shalls": [shall]})]
    client = MagicMock()
    client.chat.completions.create.side_effect = [SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=p), finish_reason="stop")]) for p in payloads]
    for key, value in {"DeepSeekConfig": lambda: SimpleNamespace(make_client=lambda: client, model="offline"), "V3_RAG": v3, "EU_JSONL": kb, "OR_JSONL": sources, "OUT_DIR": tmp_path, "OUT_FILE": tmp_path / "new_diagnostic.json"}.items():
        monkeypatch.setitem(ns, key, value)
    main()
    out = json.loads((tmp_path / "new_diagnostic.json").read_text(encoding="utf-8"))["result_sets"][0]
    assert out["_evidence_selection"]["input_ids"] == ["E-test"]
    assert out["_evidence_selection"]["selected_ids"] == ["E-test"]
    assert out["_extraction_status"] == {"E-test": "success"}
    assert out["engineering_requirements"][0]["_grade"] == "B"
    assert client.chat.completions.create.call_count == 2
    prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert '\"unit\": \"dGH\"' in prompt
    assert "fresh water" in prompt
