import ast,copy,json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from cooling_rag_mg.ea_ui_export import export_ea_payload_bytes,native_exporter
from cooling_rag_mg.ea_presentation import presentation_xml
from cooling_rag_mg.ea_structure import q,properties

def inputs():
    src=[{'requirement_id':'REQ-src','topic':'Cooling availability','requirement_text':'Cooling shall work.\nKeep original source.'}]
    payload={'confidence':0.47,'requirement_sets':[{'source_requirement_id':'REQ-src','engineering_requirements':[{'id':'ER-alpha','parent_id':'REQ-src','topic':'Valve temperature','shall_statement':'Valve shall work at 80 °C.\nComplete text.','acceptance_criteria':['80 °C'],'evidence_ids':['E-valid'],'support_status':'need_confirmation','confidence':0.17},{'id':'ER-child','parent_id':'ER-alpha','topic':'Sensor verification','shall_statement':'Sensor shall be verified.','acceptance_criteria':['TBD'],'evidence_ids':[]}],'relationships':[{'source':'ER-alpha','target':'ER-child','type':'refine'}],'evidence_gaps':[{'description':'Keep gap'}]}]}
    kb={'E-valid':{'kb_tier':'L2','text':'80 °C','metadata':{'source_document':'Manual'}}}
    return payload,src,kb

def test_ui_native_ids_parent_grade_and_lossless_payload():
    p,s,k=inputs();before=copy.deepcopy(p)
    root=ET.fromstring(export_ea_payload_bytes(p,source_requirements=s,kb_index=k));props=properties(root);by={v['id']:(r,v) for r,v in props.items()}
    assert set(by)=={'REQ-src','ER-alpha','ER-child'};assert p==before
    assert by['ER-alpha'][1]['grade']=='B';assert by['ER-child'][1]['grade']=='C'
    assert by['ER-alpha'][1]['text']=='<memo>#NOTES#'+p['requirement_sets'][0]['engineering_requirements'][0]['shall_statement']
    assert json.loads(by['REQ-src'][1]['ui_payload_json'].removeprefix('<memo>#NOTES#'))==p
    assert json.loads(by['ER-alpha'][1]['ui_original_json'].removeprefix('<memo>#NOTES#'))['confidence']==0.17
    ends=[[e.get('type') for e in a.iter(q('AssociationEnd'))] for a in root.iter(q('Association'))]
    assert [by['ER-alpha'][0],by['ER-child'][0]] in ends
    for role in root.iter(q('ClassifierRole')):
        r=role.get('xmi.id');doc=next(t.get('value') for t in role.iter(q('TaggedValue')) if t.get('tag')=='documentation')
        assert doc==props[r]['text'].removeprefix('<memo>#NOTES#')

def test_ui_route_uses_native_exporter_and_normalized_records():
    s=Path('ui/pages/engineering.py').read_text(encoding='utf-8');tree=ast.parse(s)
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='export_ea_payload_bytes']
    assert len(calls)==1
    kw={x.arg:x.value for x in calls[0].keywords};assert isinstance(kw['source_requirements'],ast.Call) and kw['source_requirements'].func.id=='normalize_df'
    assert 'requirements_ea_folded.xml' in s and 'export_payload_bytes(payload)' not in s

@pytest.mark.parametrize('failure',['missing_source','duplicate','parent','cycle'])
def test_ui_rejects_invalid_identity_or_structure(failure):
    p,s,k=inputs();req=p['requirement_sets'][0]['engineering_requirements']
    if failure=='missing_source':s=[]
    if failure=='duplicate':req[1]['id']='ER-alpha'
    if failure=='parent':req[1]['parent_id']='unknown'
    if failure=='cycle':req[0]['parent_id']='ER-child'
    with pytest.raises(ValueError):export_ea_payload_bytes(p,source_requirements=s,kb_index=k)

@pytest.mark.parametrize('grade,criterion,citations,kb',[('A','80 °C',[{'kb_id':'L1-a'}],{'L1-a':{'kb_tier':'L1','text':'Clause 2.1 80 °C'}}),('B','80 °C',[{'kb_id':'E-a'}],{'E-a':{'kb_tier':'L2','text':'80 °C'}}),('C','{{TBD|source}}',[],{}),('X','80 °C',[],{})])
def test_grade_is_rule_not_probability(grade,criterion,citations,kb):
    from cooling_rag_mg.grade_classifier import classify_grade
    assert classify_grade(criterion,citations,kb)==grade

def test_fold_expand_preserves_properties_and_only_changes_display():
    p,s,k=inputs();a=ET.fromstring(export_ea_payload_bytes(p,source_requirements=s,kb_index=k));ea=native_exporter()
    folded=ET.fromstring(presentation_xml(ET.tostring(a,encoding='unicode'),ea.GRADE_STYLE))
    expanded=ET.fromstring(presentation_xml(ET.tostring(a,encoding='unicode'),ea.GRADE_STYLE,expanded_ids=['ER-alpha']))
    assert properties(a)==properties(folded)==properties(expanded)
    nodes=lambda r:{x.get('subject'):x for x in r.iter(q('DiagramElement'))}
    rid=next(r for r,v in properties(a).items() if v['id']=='ER-alpha')
    assert 'Notes=0;' not in nodes(folded)[rid].get('style');assert 'Notes=0;' in nodes(expanded)[rid].get('style')
    assert 'text' in next(t.get('value') for d in folded.iter(q('Diagram')) for t in d.iter(q('TaggedValue')) if t.get('tag')=='styleex').split('SUPTAG=')[1].split(';')[0].split(',')

def test_default_cli_emits_folded_native_view(tmp_path,monkeypatch):
    from cooling_rag_mg.ea_presentation import serialize
    p,s,k=inputs();source=tmp_path/'source.xml';source.write_bytes(export_ea_payload_bytes(p,source_requirements=s,kb_index=k))
    import sys
    monkeypatch.setattr(sys,'argv',['export','--input-xmi',str(source),'--out-dir',str(tmp_path/'out')])
    native_exporter().main()
    result=ET.parse(tmp_path/'out/source_folded.xml').getroot()
    assert next(result.iter(q('Package'))).get('name').startswith('Presentation_')
    assert properties(result)==properties(ET.parse(source).getroot())
