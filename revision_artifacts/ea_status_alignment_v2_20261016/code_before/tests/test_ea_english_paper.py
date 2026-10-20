import json
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from cooling_rag_mg.ea_paper_figures import paper_bundle
from cooling_rag_mg.ea_structure import q,properties

ROOT=Path(__file__).resolve().parents[1]/'revision_artifacts/ea_english_small_figures_20261016'
def inputs():return (ROOT/'source.xml').read_text(encoding='utf-8'),json.loads((ROOT/'selection_translation_map.json').read_text(encoding='utf-8'))
def test_full_contents_and_selected_views():
    xml,m=inputs();before=properties(ET.fromstring(xml));outputs=paper_bundle(xml,m)
    for f in m['figures']:
        root=ET.fromstring(outputs[f['name']+'.xml']);after=properties(root)
        assert len(after)==23
        assert len(list(root.iter(q('Association'))))==20
        by={p['id']:p for p in after.values()}
        for original_guid,p in before.items():
            assert all(by[p['id']][key]==value for key,value in p.items())
            assert by[p['id']]['paper_original_text']==p['text']
            assert by[p['id']]['paper_source_guid']==original_guid
        roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))}
        visible=[after[e.get('subject')]['id'] for e in root.iter(q('DiagramElement')) if e.get('subject') in roles]
        assert set(visible)==set(f['ids'])
        assert all(len(e.get('name'))<=48 for e in roles.values())
        assert all('Notes=0;' not in e.get('style','') for e in root.iter(q('DiagramElement')))
@pytest.mark.parametrize('issue',['stale','number','missing','chinese','size'])
def test_rejects_unsafe_mapping(issue):
    xml,m=inputs();r=m['requirements']['OR008.1']
    if issue=='stale':r['original_text']='wrong'
    if issue=='number':r['english_text']=r['english_text'].replace('79','90');r['translation_reviewed']=True
    if issue=='missing':del m['requirements']['OR008']
    if issue=='chinese':r['english_title']='温度'
    if issue=='size':m['figures'][0]['ids']=['OR008']
    with pytest.raises(ValueError):paper_bundle(xml,m)
def test_ui_entry_preserves_latest_source_restore():
    path=Path(__file__).resolve().parents[1]/'ui/pages/engineering.py'
    text=path.read_text(encoding='utf-8')
    before=(ROOT/'engineering_before.py').read_text(encoding='utf-8')
    assert text[:text.index('    # ── Export row')].replace('from cooling_rag_mg.ea_paper_figures import mapping_template, paper_zip\n','')==before[:before.index('    # ── Export row')]
    assert 'paper_zip(xml_bytes, json.loads(figure_mapping.getvalue()))' in text

def test_explicit_native_frame_reserves_caption_band():
    import re
    xml,m=inputs();files=paper_bundle(xml,m)
    for f in m['figures']:
        root=ET.fromstring(files[f['name']+'.xml']);package=next(root.iter(q('Package')))
        frame=next(e for e in root.iter(q('DiagramElement')) if e.get('subject')==package.get('xmi.id'))
        assert 'Top=10;' in frame.get('geometry')
        roles={e.get('xmi.id') for e in root.iter(q('ClassifierRole'))}
        assert all(int(re.search('Top=(\\d+)',e.get('geometry'))[1])>=60 for e in root.iter(q('DiagramElement')) if e.get('subject') in roles)
