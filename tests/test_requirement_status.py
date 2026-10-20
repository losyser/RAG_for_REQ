import xml.etree.ElementTree as ET
from cooling_rag_mg.requirement_status import normalize_status,display_colors,colorref
from cooling_rag_mg.ea_status_view import status_view
from cooling_rag_mg.ea_structure import properties,q
import runpy
inputs=runpy.run_path('tests/test_ea_folded_ui.py')['inputs']
from cooling_rag_mg.ea_ui_export import export_ea_payload_bytes

def test_reported_direct_never_promoted_by_self_assertions():
    s=normalize_status({'support_status':'verified_by_direct_evidence','grade':'B','derivation':'Direct','semantic_support_verified':True})
    assert s['evidence_support_state']=='reported_direct'
    assert s['evidence_support_label']=='Reported direct (unverified)'
    assert s['semantic_verification_state']=='not_assessed'
    assert normalize_status({'grade':'A','derivation':'Direct'})['evidence_support_state']=='not_assessed'

def test_explicit_grade_is_preserved_even_when_criterion_would_differ():
    s=normalize_status({'_grade':'B','measurable_criterion':'TBD','support_status':'evidence_gap'}, {})
    assert s['rule_grade']=='B'
    assert s['evidence_support_state']=='evidence_gap'

def test_two_modes_match_shared_colors_preserve_payload_and_edges():
    payload,sources,kb=inputs()
    payload['requirement_sets'][0]['engineering_requirements'][0]['support_status']='verified_by_direct_evidence'
    exports=[export_ea_payload_bytes(payload,source_requirements=sources,kb_index=kb,coloring_by=mode,batch_id='test-batch') for mode in ['Rule grade','Evidence support']]
    for mode,xml in zip(['Rule grade','Evidence support'],exports):
        root=ET.fromstring(xml);props=properties(root)
        by={p['id']:p for p in props.values()}
        assert by['ER-alpha']['support_status']=='verified_by_direct_evidence'
        assert by['ER-alpha']['evidence_support_label']=='Reported direct (unverified)'
        assert by['ER-alpha']['status_batch_id']=='test-batch'
        assert len(list(root.iter(q('Association'))))==2
        for obj in root.iter(q('DiagramElement')):
            if obj.get('subject') in props:
                p=props[obj.get('subject')];bg,_=display_colors(p,mode)
                assert 'BCol='+str(colorref(bg))+';' in obj.get('style')
    assert {p['id']:p['grade'] for p in properties(ET.fromstring(exports[0])).values() if 'grade' in p}=={p['id']:p['grade'] for p in properties(ET.fromstring(exports[1])).values() if 'grade' in p}
