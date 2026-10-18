import pytest
from cooling_rag_mg.grade_classifier import classify_grade

@pytest.mark.parametrize('criterion',['0.3-0.6 bar','90-100°C','0.8-1.0 kW/cyl','1-3分钟','-40--20°C','-40至-20°C'])
def test_numeric_ranges_remain_numeric_with_or_without_citations(criterion):
    kb={'E-VALID':{'id':'E-VALID','kb_tier':'L2'}}
    assert classify_grade(criterion,[{'kb_id':'E-VALID'}],kb,numeric_policy='numeric-ranges-v1')=='B'
    assert classify_grade(criterion,[],kb,numeric_policy='numeric-ranges-v1')=='X'

@pytest.mark.parametrize('criterion',['E-ID-90-100°C','TE90-100°C','{{TBD|hint:90-100°C}}','component_90-100°C'])
def test_range_support_does_not_turn_ids_or_deferrals_into_values(criterion):
    assert classify_grade(criterion,[],{},numeric_policy='numeric-ranges-v1')=='C'


def test_range_policy_is_optional_and_versioned():
    from cooling_rag_mg.grade_classifier import classify_result_set
    row={'measurable_criterion':'90-100°C','evidence_citations':[]}
    rs={'engineering_requirements':[row]}
    legacy=classify_result_set(rs,{})['engineering_requirements'][0]
    opted=classify_result_set(rs,{},numeric_policy='numeric-ranges-v1')['engineering_requirements'][0]
    assert legacy['_grade']=='C'
    assert opted['_grade']=='X'
    assert legacy['_grade_version'] != opted['_grade_version']
    assert row == rs['engineering_requirements'][0]
    with pytest.raises(ValueError):
        classify_grade('90°C',[],{},numeric_policy='typo')
