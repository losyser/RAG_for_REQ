import copy
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from cooling_rag_mg.ea_paper_figures import paper_bundle, mapping_template
from cooling_rag_mg.ea_structure import q, properties

ROOT = Path(__file__).resolve().parents[1] / 'revision_artifacts/ea_paper_v4_20261016'

def inputs():
    return ((ROOT / 'audit/source.xml').read_text(encoding='utf-8'),
            json.loads((ROOT / 'audit/selection_translation_map.json').read_text(encoding='utf-8')))

def edges(root):
    props = properties(root)
    return {tuple(props[e.get('type')]['id'] for e in a.iter(q('AssociationEnd')))
            for a in root.iter(q('Association'))}

def test_combined_and_split_preserve_hierarchy_content_and_status():
    xml, mapping = inputs()
    source = ET.fromstring(xml)
    original = {p['id']: (rid,p) for rid,p in properties(source).items()}
    files = paper_bundle(xml,mapping)
    assert len([k for k in files if k.endswith('.xml')]) == 4
    for name, data in files.items():
        if not name.endswith('.xml'): continue
        root = ET.fromstring(data)
        props = properties(root)
        roles = {r.get('xmi.id'):r for r in root.iter(q('ClassifierRole'))}
        selected = {p['id'] for p in props.values()}
        assert len(roles) == (15 if 'combined' in name else 5)
        assert edges(root) == {edge for edge in edges(source) if set(edge) <= selected}
        ids = [e.get('xmi.id') for e in root.iter() if e.get('xmi.id')]
        assert len(ids) == len(set(ids))
        for rid,role in roles.items():
            p = props[rid]; bid = p['id']; old_guid,old = original[bid]
            row = mapping['requirements'][bid]
            assert role.get('name') == row['english_title'] != bid
            assert p['text'] == '<memo>#NOTES#' + row['english_text']
            assert p['paper_original_text'] == old['text']
            assert p['paper_source_guid'] == old_guid
            for key,value in old.items():
                if key != 'text': assert p[key] == value, (bid,key)
            tags = {t.get('tag'):t.get('value') for t in role.iter(q('TaggedValue'))}
            assert tags['documentation'] == row['english_text']
        diagrams = list(root.iter(q('Diagram')))
        assert len(diagrams) == (3 if 'combined' in name else 1)
        for diagram in diagrams:
            figure = next(f for f in mapping['figures'] if f['title'] == diagram.get('name'))
            objects = {props[e.get('subject')]['id']:e for e in diagram.iter(q('DiagramElement')) if e.get('subject') in roles}
            assert set(objects) == set(figure['ids'])
            rects = {bid:{k:int(v) for k,v in re.findall(r'(Left|Top|Right|Bottom)=(\d+)',e.get('geometry'))} for bid,e in objects.items()}
            rr=rects[figure['root_id']]
            assert all(rr['Bottom'] < r['Top'] for bid,r in rects.items() if bid != figure['root_id'])
            assert abs((rr['Left']+rr['Right']) - (min(r['Left'] for r in rects.values())+max(r['Right'] for r in rects.values()))) <= 1
            if figure['root_id'] in ('R001','R004'):
                assert len({r['Top'] for bid,r in rects.items() if bid != figure['root_id']}) == 1
    combined=ET.fromstring(files['paper_v4_combined.xml'])
    assert ('ER-R002-01','ER-R002-01-01') in edges(combined)
    assert ('R002','ER-R002-01-01') not in edges(combined)

@pytest.mark.parametrize('issue',['stale','number','missing','root','mode','provenance'])
def test_bad_selection_or_translation_rejected(issue):
    xml,m=inputs();m=copy.deepcopy(m)
    row=m['requirements']['ER-R002-01']
    if issue=='stale':row['original_text']='wrong'
    if issue=='number':row['english_text']=row['english_text'].replace('36','37')
    if issue=='missing':del m['requirements']['R001']
    if issue=='root':m['figures'][0]['root_id']='ER-R001-01'
    if issue=='mode':m['coloring_mode']='Rule grade'
    if issue=='provenance':del row['translation_status']
    with pytest.raises(ValueError):paper_bundle(xml,m)

def test_template_and_ui_default_evidence_support():
    xml,_=inputs()
    assert mapping_template(xml)['paper_profile']=='landscape_v4'
    assert mapping_template(xml)['coloring_mode']=='Evidence support'
    ui=(ROOT.parents[1]/'ui/pages/engineering.py').read_text(encoding='utf-8')
    assert 'index=1' in ui[ui.index('key="ea_coloring_by"')-150:ui.index('key="ea_coloring_by"')]
