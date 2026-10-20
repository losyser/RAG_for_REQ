from pathlib import Path
import sys,json,xml.etree.ElementTree as ET,collections
from playwright.sync_api import sync_playwright
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.requirement_status import display_colors
O=R/'revision_artifacts/ea_status_alignment_v2_20261016';out=O/'browser';out.mkdir(exist_ok=True)
record=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page(accept_downloads=True,viewport={'width':1600,'height':1100})
 page.goto('http://127.0.0.1:8501',wait_until='domcontentloaded');page.get_by_role('button',name='工程化需求',exact=True).wait_for(timeout=45000);page.get_by_role('button',name='工程化需求',exact=True).click()
 page.get_by_role('button',name='加载已保存结果',exact=True).wait_for(timeout=30000)
 for dataset,batch,marker in [('cn98','batch_20260730_164747\\engineering_requirements_20260730_164801\\engineering_requirements.json','ER-R001'),('en23','batch_status_v2_en23_acceptance\\engineering_requirements_acceptance\\engineering_requirements.json','RS-OR041')]:
  label=page.get_by_text('加载已保存的工程化结果（离线）',exact=True)
  if label.locator('xpath=ancestor::details').get_attribute('open') is None:label.click()
  page.get_by_role('combobox',name='已保存结果').click();page.get_by_role('option',name=batch,exact=True).click()
  page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000);page.get_by_role('button',name='加载已保存结果',exact=True).click()
  page.get_by_text(marker,exact=True).wait_for(timeout=30000);page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
  for mode,short in [('Rule grade','rule'),('Evidence support','support')]:
   page.get_by_text(mode,exact=True).click();page.get_by_test_id('stStatusWidget').wait_for(state='hidden',timeout=30000)
   page.wait_for_function("arg => {let els=[...document.querySelectorAll('.sysml-block')];return els.length===arg.count && els.every(e=>e.dataset.coloringMode===arg.mode)}",arg={'count':98 if dataset=='cn98' else 20,'mode':mode},timeout=45000)
   expected_first='rgb(255, 245, 210)' if mode=='Rule grade' else 'rgb(216, 240, 236)' if dataset=='cn98' else 'rgb(241, 243, 245)'
   page.wait_for_function("expected => getComputedStyle(document.querySelector('.sysml-block')).backgroundColor===expected",arg=expected_first,timeout=30000)
   rows=page.locator('.sysml-block').evaluate_all("els => els.map(e => ({id:e.querySelector('.sysml-attr').textContent.split(':').slice(1).join(':').trim(),grade:e.dataset.ruleGrade,support:e.dataset.supportState,bg:getComputedStyle(e).backgroundColor,label:e.querySelector('.badge').textContent}))")
   with page.expect_download(timeout=30000) as event:page.get_by_role('button',name='导出 EA 原生 XMI（默认折叠）',exact=True).click()
   target=out/(dataset+'_'+short+'.xml');event.value.save_as(target)
   props=properties(ET.parse(target).getroot());by={v['id']:v for v in props.values()}
   assert len(rows)==(98 if dataset=='cn98' else 20)
   for row in rows:
    v=by[row['id']];assert row['grade']==v['rule_grade'] and row['support']==v['evidence_support_state']
    hexcolor=display_colors(v,mode)[0];rgb='rgb('+', '.join(str(int(hexcolor[i:i+2],16)) for i in (1,3,5))+')';assert row['bg']==rgb,(row,rgb)
    assert 'Verified' not in row['label']
   (out/(dataset+'_'+short+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
   page.get_by_text(mode,exact=True).scroll_into_view_if_needed();page.screenshot(path=str(out/(dataset+'_'+short+'.png')))
   record.append({'dataset':dataset,'mode':mode,'nodes_compared':len(rows),'support_counts':dict(collections.Counter(r['support'] for r in rows)),'grade_counts':dict(collections.Counter(r['grade'] for r in rows)),'UI_EA_download_match':True})
  # The real Chinese content cannot be represented as an English paper export without review.
  if dataset=='cn98':
   page.get_by_text('English paper figures / 英文论文分图',exact=True).click()
   with page.expect_download() as event:page.get_by_role('button',name='Download English figure mapping template',exact=True).click()
   temp=out/'cn_template.json';event.value.save_as(temp);mapping=json.loads(temp.read_text(encoding='utf-8'))
   mapping['figures']=[{'name':'case_'+str(i),'ids':['R001','ER-R001-01','ER-R001-02'],'rationale':'English-language rejection check'} for i in range(3)]
   temp.write_text(json.dumps(mapping,ensure_ascii=False),encoding='utf-8');page.locator('input[type=file]').set_input_files(str(temp))
   page.get_by_text('English figure mapping: Concise English title and English text required: R001',exact=True).wait_for(timeout=30000)
   record.append({'chinese_paper_output_without_translation_rejected':True})
 (out/'acceptance.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2));b.close()
