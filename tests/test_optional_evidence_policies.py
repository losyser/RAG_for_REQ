import copy
import json
from unittest.mock import MagicMock, patch

import pytest

from cooling_rag_mg.coverage_retrieval import aligned_retrieve
from cooling_rag_mg.evidence_contracts import select_evidence, SELECTION_POLICY, MIXED_SELECTION_POLICY
from cooling_rag_mg.generation_risks import assess_generation_risks, annotate_generation_risks, RISK_POLICY


def evidence(n=14):
    return [{"id": f"E{i}", "text": "<= 10 bar", "_extracted_values":
             [{"value_text": "10", "operator": "<=", "unit": "bar"}] if i < n-1 else []}
            for i in range(n)]


@pytest.mark.parametrize("limit", [1, 2, 12, 20])
def test_selection_versions(limit):
    ev = evidence()
    before = copy.deepcopy(ev)
    old = select_evidence(ev, limit)
    new = select_evidence(ev, limit, policy=MIXED_SELECTION_POLICY)
    assert old == select_evidence(ev, limit, policy=SELECTION_POLICY)
    assert len(new) == min(limit, len(ev))
    assert len({e['id'] for e in new}) == len(new)
    assert ev == before
    if 1 < limit < 14:
        assert new[:-1] == old[:-1] and new[-1]['id'] == 'E13'
    else:
        assert new == old


@pytest.mark.parametrize("pairs,hits,rescue", [([], [], False), ([('pipe', 'material')], [], True),
                                               ([('pipe', 'material')], [{'id': 'hit'}], False)])
def test_rescue_only_at_zero_hit_boundary(pairs, hits, rescue):
    searcher = MagicMock()
    searcher.filtered_vector_search.return_value = hits
    searcher.filtered_bm25_search.return_value = hits
    searcher.vector_search.return_value = [{'id': 'other'}, {'id': 'second'}]
    searcher.bm25_search.return_value = [{'id': 'other'}]
    diag = {}
    with patch('cooling_rag_mg.requirement_analyzer.analyze_requirement', return_value=pairs):
        rows, used = aligned_retrieve('req', searcher, None, 'mock', max_total=1,
            diagnostics=diag, policy='zero-hit-unfiltered-rescue-v1')
    assert used == pairs and len(rows) == 1
    assert diag['unfiltered_rescue_attempted'] == rescue
    if rescue:
        assert rows[0]['_mapping_applicability'] == 'unknown'
        assert diag['nonempty_mapping_zero_results']
    if pairs and hits:
        searcher.vector_search.assert_not_called()


def test_legacy_never_rescues_and_invalid_policy_fails_before_analyzer():
    s = MagicMock()
    s.filtered_vector_search.return_value = s.filtered_bm25_search.return_value = []
    with patch('cooling_rag_mg.requirement_analyzer.analyze_requirement', return_value=[('pipe','material')]) as a:
        assert aligned_retrieve('req', s, None, 'mock')[0] == []
        s.vector_search.assert_not_called()
        with pytest.raises(ValueError):
            aligned_retrieve('req', s, None, 'mock', policy='typo')
        assert a.call_count == 1


@pytest.mark.parametrize("claim,expected", [('<= 10 bar','lexical_tuple_match_only'),
    ('>= 10 bar','unmatched_requires_review'), ('<= 10 MPa','unmatched_requires_review'),
    ('<= -10 bar','unmatched_requires_review'), ('TBD','unknown_no_recognized_quantity')])
def test_risks_do_not_promote_matching_numbers(claim, expected):
    row = {'shall_statement': claim, 'evidence_ids': ['E0'], 'support_status':'verified_by_direct_evidence'}
    result = annotate_generation_risks([row], evidence(), policy=RISK_POLICY)[0]
    report = result['_independent_risks']
    assert report['numeric_consistency'] == expected
    assert report['semantic_support'] == report['applicability'] == 'unknown'
    assert report['unknown_applicability_fields']
    assert result['support_status'] == 'need_confirmation'
    assert row['support_status'] == 'verified_by_direct_evidence'
    assert annotate_generation_risks([row], evidence())[0] == row


def test_missing_scope_and_ambiguous_ids():
    row = {'shall_statement':'10 bar', 'evidence_ids':['E0', 'forged']}
    assert assess_generation_risks(row, None)['citation_existence'] == 'unknown'
    report = assess_generation_risks(row, [{'id':'E0','text':'10 bar'}, {'id':'E0','text':'20 bar'}])
    assert report['missing_ids'] == ['forged']
    assert 'ambiguous_duplicate_citation' in report['issues']
    assert report['numeric_consistency'] == 'unmatched_requires_review'


def test_real_generator_with_mock_completion_and_selected_scope():
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    row = {'shall_statement':'<= 10 bar', 'measurable_criterion':'<= 10 bar',
           'applicable_condition':'unknown', 'verification_method':'test', 'acceptance_criteria':['<= 10 bar'],
           'evidence_citations':[{'kb_id':'E13','tier':'L2','source':'fixture','has_clause':False}]}
    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({'shalls':[row]})))])
    legacy = generate_structured_shalls('req', evidence(), client, 'mock')
    assert legacy == [row]
    result = generate_structured_shalls('req', evidence(), client, 'mock',
        selection_policy=MIXED_SELECTION_POLICY, risk_policy=RISK_POLICY)
    assert result[0]['_independent_risks']['citation_existence'] == 'present'
    assert '[E13]' in client.chat.completions.create.call_args.kwargs['messages'][0]['content']
    with pytest.raises(ValueError):
        generate_structured_shalls('req', evidence(), client, 'mock', risk_policy='typo')
    assert client.chat.completions.create.call_count == 2


def test_ui_normalizer_opt_in_independent_risk():
    from cooling_rag_mg.engineering_requirement_agent import normalize_agent_output
    row = {'id':'R1-ER1','shall_statement':'<= 10 bar', 'acceptance_criteria':['<= 10 bar'],
           'evidence_ids':['E0'], 'support_status':'verified_by_direct_evidence'}
    out = normalize_agent_output({'engineering_requirements':[row]}, 'R1', evidence_scope=evidence(), risk_policy=RISK_POLICY)
    assert out['engineering_requirements'][0]['_independent_risks']['semantic_support'] == 'unknown'
    assert out['engineering_requirements'][0]['support_status'] != 'verified_by_direct_evidence'


def test_selection_bad_policy_and_duplicate_fail():
    with pytest.raises(ValueError):
        select_evidence(evidence(), policy='typo')
    with pytest.raises(ValueError):
        select_evidence([{'id':'x'}, {'id':'x','text':'different'}], policy=MIXED_SELECTION_POLICY)


@pytest.mark.parametrize('mode', ['normal', 'repaired', 'fallback', 'budget'])
def test_ui_graph_risk_policy_all_paths(monkeypatch, mode):
    from types import SimpleNamespace
    from cooling_rag_mg import engineering_requirement_agent as agent
    row = {'id':'R1-ER1', 'shall_statement':'<= 10 bar', 'evidence_ids':['E0','forged'],
           'acceptance_criteria':['<= 10 bar'], 'support_status':'verified_by_direct_evidence'}
    obj = {'engineering_requirements':[row]}
    monkeypatch.setattr(agent, 'compact_requirement_context', lambda c: {'supported_evidence':evidence(), 'allowed_engineering_aspects':[]})
    monkeypatch.setattr(agent, 'get_config', lambda: SimpleNamespace(deepseek=SimpleNamespace(
        enabled=True, make_client=lambda: object(), model='mock', temperature=0, max_tokens_requirement_agent=1000)))
    monkeypatch.setattr(agent, 'cached_completion', lambda *a, **kw: SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=json.dumps(obj) if mode == 'normal' else 'broken'))]))
    def repair(*a, **kw):
        if mode == 'fallback':
            raise ValueError('mock failure')
        return obj
    monkeypatch.setattr(agent, 'repair_json_with_deepseek', repair)
    if mode == 'budget':
        monkeypatch.setattr(agent, 'UI_MAX_PROMPT_CHARS', 1)
    out = agent.build_graph(risk_policy=RISK_POLICY).invoke({'requirement':{'requirement_id':'R1'}, 'retrieval_context':{}, 'errors':[]})['output']
    assert out['engineering_requirements']
    for result in out['engineering_requirements']:
        assert result['_independent_risks']['semantic_support'] == 'unknown'
        assert result['support_status'] != 'verified_by_direct_evidence'
    if mode in ('normal','repaired'):
        assert out['engineering_requirements'][0]['_independent_risks']['missing_ids'] == ['forged']
