import importlib.util
from pathlib import Path
import pytest
from cooling_rag_mg.review_routing import conflict_flag, derivation_assessment
from cooling_rag_mg.grade_classifier import classify_grade, valid_citation_ids
from cooling_rag_mg.revision_audit import strict_numeric_label, validate_expert_rows, validate_prediction_pool, successful_variant

def test_partial_is_not_complete_support():
    assert strict_numeric_label({'supported':['a'], 'unverifiable':['b']}, 'a | SUPPORTED | ok') == 'partial_support'
    assert strict_numeric_label({'supported':['a']}, 'a | SUPPORTED | ok') == 'all_reported_supported'
    assert strict_numeric_label({}, '') == 'unparsed'
    assert strict_numeric_label({}, 'NO_NUMERIC_CLAIMS') == 'no_numeric'
    assert strict_numeric_label({'supported':['a'],'contradicted':['b']}, '') == 'contradicted'

def test_tbd_priority_and_unicode_citation():
    kb={'L1-CCS2025-表3.9.2.2.8':{'kb_tier':'L1','metadata':{'location':'3.9.2.2.8'}}}
    assert valid_citation_ids('L1-CCS2025-表3.9.2.2.8',kb)==list(kb)
    assert classify_grade('{{TBD|unit:bar}} 5 bar',[],kb)=='C'
    assert classify_grade('5 Pa',[],kb)=='C'  # documented limitation, not semantic pass
    assert classify_grade('5 bar',[],kb)=='X'

def test_residual_derived_never_asserts_verified_math():
    kb={'E-a':{'text':'90 °C','kb_tier':'L2'}}
    d=derivation_assessment({'measurable_criterion':'88 °C','evidence_citations':[{'kb_id':'E-a'}]},kb)
    assert d['legacy_type']=='Derived' and d['mathematical_derivation_verified'] is False
    assert d['classification']=='unmatched_numeric' and d['requires_review']

def test_conflict_unit_field_and_pairwise_candidates():
    kb={x:{'text':'','kb_tier':'L2'} for x in ('E-a','E-b','E-c')}
    er={'measurable_criterion':'90 °C','evidence_citations':[{'kb_id':x} for x in kb]}
    ev={'E-a':[{'value_text':'90','unit':'°C'}], 'E-b':[{'value_text':'95','unit':'°C'}], 'E-c':[{'value_text':'90','unit':'°C'}]}
    c=conflict_flag(er,kb,ev)
    assert c and c['status']=='candidate_requires_applicability_review'
    assert len(c['candidate_pairs'])==2 and c['authority_decision'] is None

def test_expert_blanks_duplicates_missing_and_invalid_block():
    key={'S2':{'1':['OR1','pump','cooling']}}
    assert validate_expert_rows({'S2':[{'item':1,'relevant':None}]},key)
    assert validate_expert_rows({'S2':[{'item':1,'relevant':2}]},key)
    assert validate_expert_rows({'S2':[{'item':1,'relevant':0}]*2},key)
    assert validate_expert_rows({'S2':[]},key)
    assert not validate_expert_rows({'S2':[{'item':1,'relevant':0}]},key)

def test_omitted_prediction_candidate_and_source_block():
    assert validate_prediction_pool({'x':{'OR1':[['a','b']]}}, {'1':['OR1','a','c']})

def test_failed_variant_excluded():
    assert not successful_variant({'result_sets':[{'engineering_requirements':[], 'error':'HTTP 402'}]})[0]
    assert not successful_variant({'result_sets':[{'engineering_requirements':[]}]})[0]

def test_prf_zero_and_scope():
    spec=importlib.util.spec_from_file_location('score',Path('scripts/98_score_expert_workbook.py'))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert m.prf({'OR1':{('a','b')}},{'OR1':{('c','d')}})['f1']==0.0
    with pytest.raises(ValueError): m.prf({'OR2':{('a','b')}},{'OR1':{('c','d')}})

def test_single_brace_placeholder_is_deferred_not_supported():
    from cooling_rag_mg.review_routing import derivation_type
    mc='{TBD|unit:°C|hint:reference 80°C}'
    assert classify_grade(mc,[],{})=='C'
    assert derivation_type({'measurable_criterion':mc,'evidence_citations':[{'kb_id':'E-a'}]}, {'E-a':{'text':'80°C'}})=='Deferred'


def test_frozen_arm_profile_detects_swap_even_with_same_metadata(tmp_path):
    import hashlib
    from cooling_rag_mg.revision_audit import verify_frozen_arm_inputs
    d=tmp_path/'data/search_results/exp_v4';d.mkdir(parents=True)
    p=d/'rag.json';p.write_text('original')
    baseline={'files':[{'path':'data/search_results/exp_v4/rag.json','sha256':hashlib.sha256(b'original').hexdigest()}]}
    assert not verify_frozen_arm_inputs(tmp_path,{'rag':'rag.json'},baseline)
    p.write_text('other generator output with same arm label')
    assert verify_frozen_arm_inputs(tmp_path,{'rag':'rag.json'},baseline)
