import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from cooling_rag_mg.ea_structure import structure_xml, validate_structure, requirement_title, properties
from cooling_rag_mg.ea_compact import compact_xml, q

spec=importlib.util.spec_from_file_location('structure_exporter',Path('scripts/92_export_ea_native_xmi.py'))
ea=importlib.util.module_from_spec(spec);spec.loader.exec_module(ea)

def fixture():
    sets=[{'source_requirement_id':'OR001','_source_text':'Cooling shall be available.', 'engineering_requirements':[{'shall_statement':'Pump shall run at 80 °C with < 5 bar pressure.','measurable_criterion':'80 °C; < 5 bar','evidence_citations':[{'kb_id':'E-real'}]}]}]
    return ea.build_xmi(sets,{'E-real':{'text':'80 °C; < 5 bar','kb_tier':'L2'}},{'S_OR001':'Cooling Availability','E_OR001_1':'Pump Temperature and Pressure'}, {})

@pytest.mark.parametrize('compact',[False,True])
def test_model_fields_and_compartment_survive_repair(compact):
    source=fixture()
    if compact: source=compact_xml(source,ea.GRADE_STYLE)
    revised=structure_xml(source,ea.GRADE_STYLE)
    assert validate_structure(source,revised)==[]
    assert ea.validate_xmi(revised,n_reqs=2,n_edges=1)==[]
    a,b=ET.fromstring(source),ET.fromstring(revised)
    assert properties(a)==properties(b)
    assert [r.get('name') for r in b.iter(q('ClassifierRole'))]==['Cooling Availability','Pump Temperature and Pressure']
    direct=list(b.find('XMI.content'))
    assert len([x for x in direct if x.tag==q('TaggedValue') and x.get('tag') in ('id','text')])==4
    assert 'Tag=0;' not in revised and 'ShowTags=0;' not in revised
    assert '80 °C' in revised and '&lt; 5 bar' in revised

def test_title_preserves_unicode_numbers_and_whole_words():
    assert requirement_title('OR001  2号泵 Cooling 80°C','OR001')=='2号泵 Cooling 80°C'
    assert requirement_title('OR001\nValve Setting\n[C | OPEN]','OR001')=='Valve Setting'
    assert requirement_title('Auxiliary Engine Outlet Temperature Sett','OR001')=='Auxiliary Engine Outlet Temperature Setting'
    assert requirement_title('', 'OR001', 'Pump shall run.')=='Pump shall run.'
    with pytest.raises(ValueError): requirement_title('OR001','OR001')

def test_validator_rejects_hidden_tags_and_content_loss():
    source=fixture(); revised=structure_xml(source,ea.GRADE_STYLE)
    assert 'hidden id/text compartment' in validate_structure(source,revised.replace('Tag=1;','Tag=0;'))
    assert 'model properties changed' in validate_structure(source,revised.replace('80 °C','90 °C'))

def test_invalid_columns_rejected():
    with pytest.raises(ValueError): structure_xml(fixture(),ea.GRADE_STYLE,0)

def test_rejects_multirow_straight_lines_that_cross_other_nodes():
    sets=[{'source_requirement_id':'OR1','_source_text':'Pump source','engineering_requirements':[{'shall_statement':'Pump shall run.'},{'shall_statement':'Pump shall stop.'}]}]
    source=ea.build_xmi(sets,{}, {},{})
    with pytest.raises(ValueError,match='all siblings in one row'):
        structure_xml(source,ea.GRADE_STYLE,per_row=1)

def test_core_tag_filter_retains_long_metadata_but_never_hides_text():
    source=fixture();revised=structure_xml(source,ea.GRADE_STYLE)
    tree=ET.fromstring(revised)
    style=next(t.get('value') for d in tree.iter(q('Diagram')) for t in d.find(q('ModelElement.taggedValue')) if t.get('tag')=='styleex')
    hidden=set(style.split('SUPTAG=',1)[1].split(';',1)[0].split(','))
    assert {'criterion','review_route','evidence_sources','shall_zh'} <= hidden
    assert not {'id','text'} & hidden
    assert properties(ET.fromstring(source))==properties(tree)
    assert 'core id/text suppressed' in validate_structure(source,revised.replace('SUPTAG=','SUPTAG=text,'))
    for node in tree.iter(q('DiagramElement')):
        if 'SOID=' in node.get('style',''):
            assert 'TREE=V;' in node.get('style','')
            assert node.get('style','').endswith('Hidden=0;')
            assert 'Path=;' not in node.get('geometry','')

@pytest.mark.parametrize('flag',['--structure','--compact'])
def test_cli_corrects_legacy_view_and_refuses_overwrite(tmp_path,monkeypatch,flag):
    import sys
    source=tmp_path/'input.xml';source.write_text(fixture(),encoding='utf-8')
    before=source.read_bytes();out=tmp_path/'out'
    monkeypatch.setattr(sys,'argv',['export',flag,'--input-xmi',str(source),'--out-dir',str(out)])
    ea.main()
    revised=(out/'input_structure.xml').read_text(encoding='utf-8')
    assert validate_structure(source.read_text(encoding='utf-8'),revised)==[]
    assert source.read_bytes()==before
    with pytest.raises(SystemExit,match='Refusing overwrite'): ea.main()
