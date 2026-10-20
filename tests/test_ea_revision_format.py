import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
spec=importlib.util.spec_from_file_location('ea_revision',Path('scripts/92_export_ea_native_xmi.py'))
ea=importlib.util.module_from_spec(spec); spec.loader.exec_module(ea)

def test_criterion_translation_preserves_numeric_and_placeholders():
    assert ea.safe_translation('80 °C','90 °C')=='80 °C'
    assert ea.safe_translation('{{TBD|hint:80°C}}','{{TBD|hint:90°C}}')=='{{TBD|hint:80°C}}'

def test_build_single_text_separate_properties_and_valid_citations():
    sets=[{'source_requirement_id':'OR001','_source_text':'Source text','engineering_requirements':[{'shall_statement':'Pump shall run.','measurable_criterion':'80°C','evidence_citations':[{'kb_id':'E-real'},{'kb_id':'E-fake'}]}]}]
    kb={'E-real':{'kb_tier':'L2','text':'80°C','metadata':{'source_document':'Manual'}}}
    xml=ea.build_xmi(sets,kb,{}, {},4)
    root=ET.fromstring(xml)
    tvs=root.findall('.//{omg.org/UML1.3}TaggedValue')
    content=[t for t in tvs if t.get('modelElement')]
    text=[t.get('value') for t in content if t.get('tag')=='text']
    assert text==['<memo>#NOTES#Source text','<memo>#NOTES#Pump shall run.']
    assert not any('\n' in x for x in text)
    assert next(t.get('value') for t in content if t.get('tag')=='evidence_ids')=='E-real'
    assert {'criterion','grade','derivation','review_route','shall_zh','evidence_sources'} <= {t.get('tag') for t in content}
    assert 'Pump shall run.' not in [t.get('value') for t in tvs if t.get('tag')=='documentation']
    assert ea.validate_xmi(xml,n_reqs=2,n_edges=1)==[]
