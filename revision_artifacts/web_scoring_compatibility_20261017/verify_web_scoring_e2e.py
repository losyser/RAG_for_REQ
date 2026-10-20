"""Synthetic answers in isolated server storage only; production records never opened."""
import hashlib,json,os,pathlib,subprocess,sys,time,urllib.request
from playwright.sync_api import sync_playwright,expect
B=pathlib.Path(__file__).parent
APP=pathlib.Path(os.environ.get('REVIEW_APP',str(B/'expert_mapping_review/server.py')))
ROOT=pathlib.Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
PKG=pathlib.Path(r'C:\Users\yando\Desktop\需求映射正式审核_8源\formal_8_sources.assignment.json')
SCORER=ROOT/'tools/formal_mapping_scoring/score_formal_review.py'
PY312=r'C:\Users\yando\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
OUT=B/'output'/('SYNTHETIC_web_score_'+time.strftime('%H%M%S'));OUT.mkdir()
URL='http://127.0.0.1:8884/'
def api(route,body):
    req=urllib.request.Request(URL+'api/'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req))
def score(path,name):
    output=OUT/(name+'.score.json')
    r=subprocess.run([PY312,'-I',str(SCORER),'--package',str(PKG),'--manifest',str(ROOT/'revision_artifacts/expert_mapping_formal_20261017/coordinator/FROZEN_SAMPLE.json'),'--predictions',str(ROOT/'data/search_results/exp_v4/e1_predictions.json'),'--records',str(path),'--expected-reviewers','1','--output',str(output)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    return json.loads(output.read_text(encoding='utf8'))
def export(page,name):
    with page.expect_download() as d:page.locator('#backupBtn').click()
    path=OUT/(name+'.review.json');d.value.save_as(str(path));return path,json.loads(path.read_text(encoding='utf8'))
proc=subprocess.Popen([sys.executable,'-I',str(APP),'--port','8884','--data-dir',str(OUT/'SYNTHETIC_ONLY_RECORDS')],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
checks=[]
try:
    for _ in range(50):
        try:
            h=json.load(urllib.request.urlopen(URL+'api/health',timeout=1));assert h['process_id']==proc.pid and h['mode']=='isolated-test'
            assert 'formal-review-details-v2' in h['features'];break
        except OSError:time.sleep(.1)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL);page.locator('#newBtn').click();page.locator('#reviewer').fill('SYNTHETIC TEST ONLY')
        page.locator('#taskKind').select_option('formal');page.locator('#assignmentFile').set_input_files(str(PKG));page.locator('#createBtn').click()
        expect(page.locator('#sourceId')).to_have_text('OR012')
        for i in range(8):
            page.locator('#unlockBtn').click();page.locator('#confirmYes').click()
            expect(page.locator('#candidateSection')).to_be_visible()
            for j in range(page.locator('#candidates .candidate').count()):page.locator('#candidates .candidate').nth(j).locator('[data-value="relevant"]').click()
            page.locator('#coverage').check();page.locator('#reviewMinutes').fill('10');page.locator('#reviewInterrupt').fill('0');page.locator('#reviewComplete').select_option('yes')
            if i<7:page.locator('#nextBtn').click()
        path,data=export(page,'synthetic_new_complete');result=score(path,'synthetic_new_complete')
        assert result['status']=='scored',result['reasons']
        assert result['coverage'][0]['definitive_candidate_count']==75
        for a in data['task']['answers'].values():
            assert a['review_details']['first_pass_at'] and a['review_details']['first_candidate_at'] and a['review_details']['exposure']=='after_first_pass'
        checks.append('Installed-format formal UI => save => downloaded backup => strict scorer succeeds with synthetic complete answers')
        page.reload();expect(page.locator('#sourceId')).to_have_text('OR011')
        _,again=export(page,'synthetic_reload');assert again['task']['answers']==data['task']['answers']
        checks.append('Reload and export preserve all stage fields and answers')
        package=json.loads(PKG.read_text(encoding='utf8'))
        legacy=api('new',{'reviewer':'SYNTHETIC LEGACY ONLY','kind':'formal','package':package,'request_id':hashlib.sha256(str(OUT).encode()).hexdigest()[:32]})
        answers={sid:{k:v for k,v in a.items() if k!='review_details'} for sid,a in data['task']['answers'].items()}
        saved=api('save',{'id':legacy['task']['id'],'token':legacy['token'],'revision':0,'answers':answers,'current_index':0})
        page.evaluate('(v)=>localStorage.setItem("mapping-review-active-v1",JSON.stringify(v))',{'task':saved['task'],'token':legacy['token'],'dirty':False})
        page.reload();expect(page.locator('#sourceId')).to_have_text('OR012')
        expect(page.locator('#reviewExposure')).to_have_value('uncertain');expect(page.locator('#reviewFirstTime')).to_have_value('')
        path,old=export(page,'synthetic_legacy_missing');assert score(path,'synthetic_legacy_missing')['status']=='blocked'
        checks.append('Legacy completed judgments preserved; missing historical metadata stays blank/uncertain and blocks scoring')
        for i in range(8):
            page.locator('#reviewExposure').select_option('after_first_pass')
            page.locator('#reviewFirstTime').fill('2026-10-17T10:00:00Z');page.locator('#reviewCandidateTime').fill('2026-10-17T10:01:00Z')
            page.locator('#reviewMinutes').fill('10');page.locator('#reviewInterrupt').fill('0');page.locator('#reviewComplete').select_option('yes')
            page.locator('#note').fill('SYNTHETIC ONLY: known fixture timestamps, not human history')
            if i<7:page.locator('#nextBtn').click()
        path,fixed=export(page,'synthetic_legacy_supplemented');assert score(path,'synthetic_legacy_supplemented')['status']=='scored'
        for sid,a in fixed['task']['answers'].items():
            for key in ('candidates','initial_pairs','missing_pairs','coverage_reviewed','first_pass_done'):assert a[key]==answers[sid][key]
        checks.append('Explicit UI metadata supplementation enables scoring without changing or repeating prior judgments')
        assert not errors,errors
        browser.close()
    (OUT/'RESULT.json').write_text(json.dumps({'passed':True,'checks':checks,'application':str(APP),'synthetic_only':True,'production_records_touched':False},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'passed':len(checks),'output':str(OUT)},ensure_ascii=True))
finally:proc.terminate();proc.wait(timeout=10)
