import copy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from cooling_rag_mg.evidence_quarantine import active_flags, mask_prompt_evidence, gate_delivery, gate_ui_output


FLAGS=[{'review_id':'review-fixture','evidence_id':'RISK','status':'quarantined',
        'reason':'edition mismatch pending review','verification_scope':'fixture, no general negative-temperature prohibition'}]


def row(ids=('RISK',), value='-100°C'):
    return {'id':'ROW','shall_statement':'Temperature shall satisfy criterion','measurable_criterion':value,
        'applicable_condition':'unknown','verification_method':'test','acceptance_criteria':[value],
        'evidence_citations':[{'kb_id':i,'source':'fixture','tier':'L2','has_clause':False} for i in ids]}


def ev(eid='RISK', value='-100°C'):
    return {'id':eid,'text':'temperature '+value,'metadata':{'normalized_summary':value,'engine_model':'test'},
        'llm_judge':{'support_type':'direct'}, '_extracted_values':[{'value_text':value,'unit':'°C','operator':'='}]}


def test_prompt_masks_all_duplicate_fields_without_mutation():
    original={'supported_evidence':[ev()], 'groups':{'a':[ev()]},'healthy':ev('HEALTHY','-40°C')}
    before=copy.deepcopy(original)
    masked=mask_prompt_evidence(original,FLAGS)
    assert '-100' not in json.dumps(masked,ensure_ascii=False)
    assert '-40' in json.dumps(masked,ensure_ascii=False)
    assert 'QUARANTINED' in masked['supported_evidence'][0]['text']
    assert original==before


@pytest.mark.parametrize('ids',[('RISK',),('HEALTHY','RISK')])
def test_flagged_or_mixed_citations_withheld_not_rewritten(ids):
    original=row(ids); before=copy.deepcopy(original);report={}
    assert gate_delivery([original],FLAGS,report=report)==[]
    blocked=report['withheld'][0]
    assert blocked['status']=='blocked_numeric'
    assert blocked['diagnostic']['numeric_provenance']=='unknown_missing_or_invalid_binding'
    assert blocked['original_row']==original==before


def test_legitimate_negative_same_number_not_inferred_as_flagged_source():
    for number in ('-40°C','-100°C'):
        report={};result=gate_delivery([row(('HEALTHY',),number)],FLAGS,report=report)
        assert len(result)==1 and result[0]['measurable_criterion']==number
        assert result[0]['_quarantine_check']['semantic_support']=='unknown'
        assert result[0]['_quarantine_check']['numeric_provenance'].startswith('unknown')
        assert not report['withheld']


def test_missing_ids_and_binding_references_fail_closed():
    report={};assert gate_delivery([row(())],FLAGS,report=report)==[]
    assert report['withheld'][0]['status']=='needs_review'
    r=row(('HEALTHY',));r['parameter_bindings']=[{'evidence_id':'RISK'}]
    report={};assert gate_delivery([r],FLAGS,report=report)==[]
    assert report['withheld'][0]['diagnostic']['flagged_ids']==['RISK']
    r['parameter_bindings']=[{'evidence_id':'HEALTHY','parameter_id':'P','claim_field':'measurable_criterion'}]
    r['evidence_citations'].append({'kb_id':'RISK'})
    assert gate_delivery([r],FLAGS)==[]  # model binding cannot override a flagged citation


def test_mixed_schema_cannot_hide_flagged_id_and_unknown_ids_are_not_support():
    r=row(('HEALTHY',));r['evidence_ids']=['RISK']
    assert gate_delivery([r],FLAGS)==[]
    r=row(('INVENTED',));report={}
    assert gate_delivery([r],FLAGS,report=report,evidence_scope=[ev('HEALTHY')])==[]
    assert report['withheld'][0]['status']=='needs_review'
    assert report['withheld'][0]['diagnostic']['out_of_scope_ids']==['INVENTED']


def test_no_flags_and_released_flags_are_legacy_identity():
    rows=[row()]
    assert gate_delivery(rows,None) is rows
    assert gate_delivery(rows,[]) is rows
    released=[{**FLAGS[0],'status':'released'}]
    assert gate_delivery(rows,released) is rows
    assert mask_prompt_evidence(rows,[]) is rows


def test_ui_removes_flagged_rows_descendants_relationships_and_summary():
    bad={'id':'P','shall_statement':'Temperature -100°C','acceptance_criteria':['-100°C'],'evidence_ids':['RISK']}
    child={'id':'C','parent_id':'P','shall_statement':'Inspect','acceptance_criteria':[],'evidence_ids':['HEALTHY']}
    obj={'engineering_requirements':[bad,child],'relationships':[{'source':'P','target':'C'}],
         'professional_summary':'Set temperature -100°C','assumptions':['-100°C']}
    before=copy.deepcopy(obj);result=gate_ui_output(obj,FLAGS)
    assert result['engineering_requirements']==[] and result['relationships']==[]
    assert '-100' not in result['professional_summary']
    assert result['_delivery_status']=='needs_review'
    assert len(result['_quarantine_delivery']['withheld'])==2
    assert obj==before


def test_v4_actual_generator_masks_prompt_and_blocks_mock_response():
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    client=MagicMock();client.chat.completions.create.return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({'shalls':[row()]})))])
    report={}
    result=generate_structured_shalls('requirement',[ev()],client,'mock',quarantine_flags=FLAGS,delivery_report=report)
    assert result==[] and report['withheld'][0]['status']=='blocked_numeric'
    prompt=client.chat.completions.create.call_args.kwargs['messages'][0]['content']
    assert '-100' not in prompt and 'QUARANTINED' in prompt
    with pytest.raises(ValueError):generate_structured_shalls('req',[ev()],client,'mock',quarantine_flags=FLAGS)
    assert client.chat.completions.create.call_count==1


@pytest.mark.parametrize('mode',['normal','repaired','fallback','budget'])
def test_ui_real_graph_routes_quarantine_through_all_paths(monkeypatch,mode):
    from cooling_rag_mg import engineering_requirement_agent as agent
    record={'requirement_id':'R1','sub_requirements':[{'selected_results':[ev()]}]}
    raw={'engineering_requirements':[{'id':'ER1','shall_statement':'Temperature -100°C','acceptance_criteria':['-100°C'],
         'evidence_ids':['RISK'],'support_status':'verified_by_direct_evidence'}]}
    captured=[]
    def completion(*a,**kw):
        captured.append(kw['messages'])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(raw) if mode=='normal' else 'broken'))])
    def repair(*a,**kw):
        if mode=='fallback':raise ValueError('mock repair failure')
        return raw
    monkeypatch.setattr(agent,'get_config',lambda:SimpleNamespace(deepseek=SimpleNamespace(enabled=True,make_client=lambda:object(),model='mock',temperature=0,max_tokens_requirement_agent=1000)))
    monkeypatch.setattr(agent,'cached_completion',completion);monkeypatch.setattr(agent,'repair_json_with_deepseek',repair)
    if mode=='budget':monkeypatch.setattr(agent,'UI_MAX_PROMPT_CHARS',1)
    out=agent.generate_engineering_requirements_for_requirement({'requirement_id':'R1'}, {'requirements':[record]},quarantine_flags=FLAGS)
    if mode in ('normal','repaired'):
        assert out['engineering_requirements']==[]
        assert out['_quarantine_delivery']['withheld']
    else:
        # Conservative fallback may retain a citation-free TBD draft; it must
        # never recover a quarantined value or claim direct verification.
        assert '-100' not in json.dumps(out['engineering_requirements'],ensure_ascii=False)
        assert all(r.get('support_status')!='verified_by_direct_evidence' for r in out['engineering_requirements'])
    if captured:
        text=json.dumps(captured,ensure_ascii=False)
        assert '-100' not in text and 'QUARANTINED' in text


def test_invalid_registry_fails_before_client():
    with pytest.raises(ValueError):active_flags([FLAGS[0],FLAGS[0]])
    with pytest.raises(ValueError):active_flags([{**FLAGS[0],'status':'silently_ok'}])
