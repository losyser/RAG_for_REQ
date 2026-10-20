from pathlib import Path
import json,sys,zipfile,xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import q,properties
out=Path(__file__).parent
record={'url':'http://127.0.0.1:8501','clicks':[],'errors':[],'fixture':'Source-derived nine-node offline acceptance fixture; not new generated requirements or journal figures.'}
def model(data):
 root=ET.fromstring(data);props=properties(root);ids={r:p['id'] for r,p in props.items()}
 return {p['id']:p for p in props.values()},sorted(tuple(ids[e.get('type')] for e in edge.iter(q('AssociationEnd'))) for edge in root.iter(q('Association')))
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page(accept_downloads=True,viewport={'width':1600,'height':1100});record['browser']=b.version
 page.on('pageerror',lambda e:record['errors'].append(str(e)))
 def click(name):
  page.get_by_role('button',name=name,exact=True).click();record['clicks'].append(name)
 def snapshot(name):
  (out/(name+'.txt')).write_text(page.locator('body').inner_text(),encoding='utf-8')
 def open_loader():
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  label=page.get_by_text('加载已保存的工程化结果（离线）',exact=True)
  details=label.locator('xpath=ancestor::details')
  if details.get_attribute('open') is None:label.click()
 def download(label,name):
  button=page.get_by_role('button',name=label,exact=True);button.wait_for(timeout=30000)
  with page.expect_download(timeout=30000) as event:button.click();record['clicks'].append(label)
  d=event.value;assert d.failure() is None;d.save_as(out/name)
  record[name]={'suggested_filename':d.suggested_filename,'bytes':(out/name).stat().st_size}
 try:
  page.goto(record['url'],wait_until='domcontentloaded')
  page.get_by_role('button',name='工程化需求',exact=True).wait_for(timeout=45000);click('工程化需求')
  page.get_by_role('button',name='加载已保存结果',exact=True).wait_for(timeout=30000)
  snapshot('01_loader')
  # Select the real default batch explicitly; temporary fixture sorts first.
  page.get_by_role('combobox',name='已保存结果').click()
  page.get_by_role('option',name='batch_20260730_164747\\engineering_requirements_20260730_164801\\engineering_requirements.json',exact=True).click()
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  click('加载已保存结果')
  page.get_by_text('ER-R001',exact=True).wait_for(timeout=30000)
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  download('导出 EA 原生 XMI（默认折叠）','actual_original_before.xml')
  old,edges=model((out/'actual_original_before.xml').read_bytes());assert len(old)==128 and len(edges)==98
  snapshot('02_original_loaded')
  # Source restoration expands the current session only; no existing files change.
  open_loader()
  page.get_by_role('combobox',name='已保存结果').click()
  page.get_by_role('option',name='batch_ui_english_acceptance_20261016\\engineering_requirements_acceptance\\engineering_requirements.json',exact=True).click()
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  click('加载已保存结果')
  page.get_by_text('RS-OR041',exact=True).wait_for(timeout=30000)
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  download('导出 EA 原生 XMI（默认折叠）','fixture_original_before.xml')
  base,baseedges=model((out/'fixture_original_before.xml').read_bytes());assert len(base)==9 and len(baseedges)==6
  snapshot('03_fixture_loaded')
  page.get_by_text('English paper figures / 英文论文分图',exact=True).click()
  download('Download English figure mapping template','downloaded_mapping_template.json')
  snapshot('04_template_downloaded')
  # First verify wrong-batch mapping is rejected visibly.
  upload=page.locator('input[type=file]');assert upload.count()==1
  upload.set_input_files(str(R/'revision_artifacts/ea_english_small_figures_20261016/selection_translation_map.json'))
  page.get_by_text('English figure mapping: Mapping IDs must exactly match the current full model',exact=True).wait_for(timeout=30000)
  record['wrong_batch_rejected']=True;snapshot('05_wrong_mapping_rejected')
  m=json.loads((out/'downloaded_mapping_template.json').read_text(encoding='utf-8'))
  titles={'OR041':'Low Supply Alarm','OR041.1':'Alarm Display','OR041.2':'Cooling Pump Redundancy','OR052':'Pump Maintenance Access','OR052.1':'Direct Component Removal','OR052.4':'Manufacturer Maintenance Access','OR008':'Temperature Control','OR008.1':'High-Temperature Valve Setpoint','OR008.5':'Sensor-to-Valve Pipe Distance'}
  for bid,row in m['requirements'].items():row['english_title']=titles[bid]
  m['figures']=[{'name':'ui_alarm','ids':['OR041','OR041.1','OR041.2'],'rationale':'Offline browser acceptance: alarm fixture.'},{'name':'ui_maintenance','ids':['OR052','OR052.1','OR052.4'],'rationale':'Offline browser acceptance: maintenance fixture.'},{'name':'ui_temperature','ids':['OR008','OR008.1','OR008.5'],'rationale':'Offline browser acceptance: temperature fixture.'}]
  mapping=out/'ui_reviewed_mapping.json';mapping.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
  upload.set_input_files(str(mapping))
  download('Export English paper figures + full EA model','browser_english_paper_figures.zip')
  snapshot('06_english_downloaded');page.screenshot(path=str(out/'english_download.png'),full_page=False)
  with zipfile.ZipFile(out/'browser_english_paper_figures.zip') as z:
   manifest=json.loads(z.read('provenance.json'));assert len(manifest['packages'])==4
   record['zip_packages']=[]
   for item in manifest['packages']:
    data=z.read(item['name']+'.xml');actual,actualedges=model(data)
    assert set(actual)==set(base) and actualedges==baseedges
    assert all(actual[bid][key]==value for bid,props in base.items() for key,value in props.items())
    root=ET.fromstring(data);rp=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))}
    assert all(e.get('name')==titles[rp[r]['id']] for r,e in roles.items())
    visible=[rp[e.get('subject')]['id'] for e in root.iter(q('DiagramElement')) if e.get('subject') in roles]
    assert set(visible)==set(item['visible_ids'])
    record['zip_packages'].append({'name':item['name'],'requirements':len(actual),'relationships':len(actualedges),'visible':visible,'all_original_properties_unchanged':True})
  download('导出 EA 原生 XMI（默认折叠）','fixture_original_after.xml')
  assert model((out/'fixture_original_after.xml').read_bytes())==(base,baseedges)
  # Return this isolated browser session to the original real batch and recheck.
  open_loader()
  page.get_by_role('combobox',name='已保存结果').click()
  page.get_by_role('option',name='batch_20260730_164747\\engineering_requirements_20260730_164801\\engineering_requirements.json',exact=True).click()
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  click('加载已保存结果')
  page.get_by_text('ER-R001',exact=True).wait_for(timeout=30000)
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  download('导出 EA 原生 XMI（默认折叠）','actual_original_after.xml')
  assert model((out/'actual_original_after.xml').read_bytes())==(old,edges)
  record['original_export_regression']={'requirements':len(old),'relationships':len(edges),'before_after_semantically_identical':True}
  record['status']='passed'
 except Exception as e:
  record['status']='failed';record['failure']=repr(e);snapshot('failure_snapshot');page.screenshot(path=str(out/'failure.png'));raise
 finally:
  (out/'browser_acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(record,ensure_ascii=False,indent=2));b.close()
