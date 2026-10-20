"""Isolated UI validation: import real unlabelled pilot; make no expert judgments."""
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright, expect

BASE=Path(__file__).parent
OUT=BASE/'output/playwright'/('pilot_'+time.strftime('%H%M%S'))
OUT.mkdir(parents=True)
APP=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular\tools\expert_mapping_review\server.py')
MATERIALS=APP.parents[2]/'revision_artifacts/expert_mapping_preparation_20261017'
URL='http://127.0.0.1:8882/'
checks=[]
errors=[]
server=subprocess.Popen([sys.executable,'-I',str(APP),'--port','8882','--data-dir',str(OUT/'isolated_blank_records')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(40):
        try:
            health=json.load(urllib.request.urlopen(URL+'api/health',timeout=1))
            if server.poll() is not None or health.get('process_id') != server.pid or health.get('mode') != 'isolated-test':
                raise RuntimeError('Wrong test server instance; refusing browser actions')
            break
        except OSError:time.sleep(.15)
    else:raise RuntimeError('Test server did not start')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=False)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(URL)
        page.locator('#newBtn').click()
        page.locator('#reviewer').fill('工具验证（未作判断）')
        page.locator('#taskKind').select_option('formal')
        page.locator('#assignmentFile').set_input_files(str(MATERIALS/'expert_packet/calibration_2_sources.pilot.json'))
        page.locator('#createBtn').click()
        expect(page.locator('#newError')).to_contain_text('类型')
        checks.append('UI rejects pilot as formal')
        page.locator('#taskKind').select_option('pilot')
        with page.expect_response(lambda response:response.url.endswith('/api/new')) as response:
            page.locator('#createBtn').click()
        task=response.value.json()['task']
        expect(page.locator('#sourceId')).to_have_text('OR002')
        expect(page.locator('#taskLabel')).to_contain_text('试做校准')
        expect(page.locator('#candidateSection')).not_to_be_visible()
        expect(page.locator('#taxonomySummary')).to_contain_text('21')
        expect(page.locator('#taxonomySummary')).to_contain_text('59')
        assert len(task['package']['sources'][0]['candidates'])==9
        assert all(not a['first_pass_done'] and not a['initial_pairs'] and not a['missing_pairs'] and set(a['candidates'].values())=={'unanswered'} for a in task['answers'].values())
        checks.append('Real pilot imports blank with independent first pass and full taxonomy')
        page.screenshot(path=str(OUT/'pilot_OR002.png'),full_page=True)
        page.locator('#nextBtn').click()
        expect(page.locator('#sourceId')).to_have_text('OR001')
        page.locator('#taxonomyDetails').evaluate('(el)=>el.open=true')
        expect(page.locator('#taxonomyAll')).to_contain_text('[原目录行注释]')
        assert page.locator('#taxonomyAll p').count()==21
        checks.append('Second real source and 21 component taxonomy render')
        page.screenshot(path=str(OUT/'pilot_taxonomy.png'),full_page=True)
        browser.close()
    package=json.loads((MATERIALS/'expert_packet/calibration_2_sources.pilot.json').read_text(encoding='utf8'))
    body={'kind':'formal','package':package,'reviewer':'tool-validation','request_id':'e'*32}
    req=urllib.request.Request(URL+'api/new',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    try:
        urllib.request.urlopen(req).close();raise AssertionError('Server accepted mismatched phase')
    except urllib.error.HTTPError as error:
        assert error.code==400;error.close()
    checks.append('HTTP independently rejects mismatched phase')
    assert not errors,errors
    (OUT/'results.json').write_text(json.dumps({'checks':checks,'page_errors':errors,'no_expert_judgments_entered':True},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'passed':len(checks),'output':str(OUT)}))
finally:
    server.terminate();server.wait(timeout=10)
