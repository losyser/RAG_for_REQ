from pathlib import Path
import sys,json,zipfile,xml.etree.ElementTree as ET,re
from playwright.sync_api import sync_playwright
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R));O=R/'revision_artifacts/ea_paper_v4_20261016';out=O/'audit/browser';out.mkdir(parents=True,exist_ok=True)
from cooling_rag_mg.ea_structure import q,properties
original=json.loads((O/'audit/selection_translation_map.json').read_text(encoding='utf-8'));results=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page(accept_downloads=True,viewport={'width':1600,'height':1100});page.goto('http://127.0.0.1:8501',wait_until='domcontentloaded')
 page.get_by_role('button',name='工程化需求',exact=True).wait_for(timeout=45000);page.get_by_role('button',name='工程化需求',exact=True).click();page.get_by_role('button',name='加载已保存结果',exact=True).wait_for(timeout=30000)
 label=page.get_by_text('加载已保存的工程化结果（离线）',exact=True)
 if label.locator('xpath=ancestor::details').get_attribute('open') is None:label.click()
 page.get_by_role('combobox',name='已保存结果').click();page.get_by_role('option',name='batch_20260730_164747\\engineering_requirements_20260730_164801\\engineering_requirements.json',exact=True).click();page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000);page.get_by_role('button',name='加载已保存结果',exact=True).click();page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
 for mode,short in [('Evidence support','support')]:
  page.get_by_text(mode,exact=True).click();page.wait_for_function("m => [...document.querySelectorAll('.sysml-block')].length===98 && [...document.querySelectorAll('.sysml-block')].every(e=>e.dataset.coloringMode===m)",arg=mode,timeout=45000);page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  label=page.get_by_text('English paper figures / 英文论文分图',exact=True)
  if label.locator('xpath=ancestor::details').get_attribute('open') is None:label.click()
  with page.expect_download() as event:page.get_by_role('button',name='Download English figure mapping template',exact=True).click()
  mapping_path=out/('mapping_'+short+'.json');event.value.save_as(mapping_path);m=json.loads(mapping_path.read_text(encoding='utf-8'));assert set(original['requirements']) <= set(m['requirements'])
  m=original.copy()
  m['figures']=original['figures'];mapping_path.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');page.locator('input[type=file]').set_input_files(str(mapping_path))
  button=page.get_by_role('button',name='Export landscape English paper figures',exact=True);button.wait_for(timeout=30000);page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  with page.expect_download() as event:button.click()
  bundle=out/('paper_'+short+'.zip');event.value.save_as(bundle)
  with zipfile.ZipFile(bundle) as z:
   names=[n for n in z.namelist() if n.endswith('.xml')];assert len(names)==4 and not any('full' in n for n in names)
   counts=[]
   for f in m['figures']:
    root=ET.fromstring(z.read(f['name']+'.xml'));props=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))};assert len(props)==5;assert not list(root.iter(q('Comment')))
    visible=[e.get('subject') for e in root.iter(q('DiagramElement')) if e.get('subject') in roles];counts.append(len(visible))
    assert {props[r]['id'] for r in visible}==set(f['ids'])
    for rid,e in roles.items():
     assert len(e.get('name'))<=48 and not re.search(r'[\u3400-\u9fff]',e.get('name'))
     v=props[rid];assert v['coloring_mode']==mode;assert v['evidence_support_label'] != 'Verified'
     tags={t.get('tag'):t.get('value') for t in e.iter(q('TaggedValue'))};assert tags['documentation']==v['text'].removeprefix('<memo>#NOTES#')
   assert counts==[5,5,5]
  results.append({'mode':mode,'download':bundle.name,'three_small_views':counts,'complete_model_per_xml':5,'root_child_english_and_folded':True,'no_comment_legend':True,'status_semantics_preserved':True})
  page.screenshot(path=str(out/('internal_ui_'+short+'.png')))
 b.close()
(out/'acceptance.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
