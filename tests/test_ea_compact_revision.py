import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
spec=importlib.util.spec_from_file_location('ea_compact',Path('scripts/92_export_ea_native_xmi.py'))
ea=importlib.util.module_from_spec(spec);spec.loader.exec_module(ea)
from cooling_rag_mg.ea_compact import compact_xml,validate_compact,merge_style,q

def fixture():
    sets=[{'source_requirement_id':'OR1','_source_text':'Source full text','engineering_requirements':[{'shall_statement':'The pump shall maintain the specified output in all required operating conditions.','measurable_criterion':'80°C','evidence_citations':[{'kb_id':'E-a'}]}]}]
    return ea.build_xmi(sets,{'E-a':{'text':'80°C','kb_tier':'L2'}},{'S_OR1':'Pump Supply','E_OR1_1':'Pump Output'}, {})

def test_compact_preserves_full_text_ids_edges_and_color():
    original=fixture();compact=compact_xml(original,ea.GRADE_STYLE)
    assert validate_compact(original,compact,ea.GRADE_STYLE)==[]
    assert ea.validate_xmi(compact,n_reqs=2,n_edges=1,compact=True)==[]
    assert 'The pump shall maintain the specified output in all required operating conditions.' in compact
    assert '[B | CONFIRM]' in compact and 'ShowNotes=0;' in compact and 'ShowTags=0;' in compact
    assert 'GRADE COLORS' in compact

def test_style_merge_preserves_unknown_fields_and_duid():
    assert merge_style('DUID=ABCDE;Tag=1;Custom=keep;',{'Tag':0,'BCol':12})=='DUID=ABCDE;Tag=0;Custom=keep;BCol=12;'

def test_semantic_loss_is_rejected():
    original=fixture();compact=compact_xml(original,ea.GRADE_STYLE).replace('80°C','90°C')
    assert 'original model properties changed' in validate_compact(original,compact,ea.GRADE_STYLE)
