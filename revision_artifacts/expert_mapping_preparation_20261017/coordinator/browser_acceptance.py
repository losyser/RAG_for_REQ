"""Real headed Edge acceptance using isolated practice records only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect

BASE = Path(__file__).parent
OUT = BASE / 'output/playwright'
OUT.mkdir(parents=True, exist_ok=True)
RUN = OUT / ('run_' + time.strftime('%H%M%S'))
RUN.mkdir()
DATA = RUN / 'practice_records'
PROFILE = RUN / 'edge_profile'
APP = Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular\tools\expert_mapping_review\server.py')
URL = 'http://127.0.0.1:8881/'
checks = []
errors = []
server = None
def record(name):
    checks.append(name)
    print('PASS ' + name, flush=True)
def start_server():
    global server
    server = subprocess.Popen([sys.executable, '-I', str(APP), '--port','8881','--data-dir',str(DATA)], stdout=subprocess.DEVNULL, stderr=(RUN/'server.log').open('ab'), creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(40):
        try:
            health=json.load(urllib.request.urlopen(URL+'api/health',timeout=1))
            if server.poll() is not None or health.get('process_id') != server.pid or health.get('mode') != 'isolated-test':
                raise RuntimeError('Wrong test server instance; refusing browser actions')
            return
        except OSError:time.sleep(.15)
    raise RuntimeError('Test server failed to start')
def stop_server():
    global server
    if server:
        server.terminate();server.wait(timeout=10);server=None
def saved(page):
    expect(page.locator('#saveState')).to_contain_text('已保存到本机',timeout=15000)
def snapshot(page,name):
    page.screenshot(path=str(RUN/name),full_page=True)
def create(page,name):
    page.get_by_role('button',name='新建审查',exact=True).click()
    page.locator('#reviewer').fill(name)
    with page.expect_response(lambda response: response.url.endswith('/api/new')) as result:
        page.locator('#createBtn').evaluate('(el)=>{el.click();el.click();}')
    task=result.value.json()['task']
    expect(page.locator('#newDialog')).not_to_be_visible()
    return task
def export(page,button,name):
    with page.expect_download() as info:page.get_by_role('button',name=button,exact=True).click()
    target=RUN/name;info.value.save_as(target);return target
def open_file(page,path):
    with page.expect_file_chooser() as info:page.get_by_role('button',name='打开旧审查',exact=True).click()
    info.value.set_files(path)

try:
    start_server()
    with sync_playwright() as p:
        context=p.chromium.launch_persistent_context(str(PROFILE),channel='msedge',headless=False,viewport={'width':1440,'height':1000},accept_downloads=True)
        page=context.pages[0]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL)
        expect(page.locator('#welcome')).to_be_visible()
        page.get_by_role('button',name='新建审查',exact=True).click()
        page.locator('#reviewer').fill('取消不会创建')
        page.get_by_role('button',name='取消',exact=True).click()
        assert not list(DATA.glob('*.json'))
        record('cancel_new_creates_no_task')
        a=create(page,'隔离测试甲')
        assert len(list(DATA.glob('*.json')))==1
        expect(page.locator('#candidateSection')).not_to_be_visible()
        record('duplicate_click_creates_one_independent_practice_task')
        page.locator('#component').select_option('pump')
        page.locator('#intent').select_option('redundancy')
        page.locator('#pairNote').fill('仅测试：独立首判原文')
        page.get_by_role('button',name='添加配对',exact=True).click()
        page.get_by_role('button',name='完成首判，显示候选',exact=True).click()
        page.locator('#confirmNo').click()
        expect(page.locator('#candidateSection')).not_to_be_visible()
        page.get_by_role('button',name='完成首判，显示候选',exact=True).click()
        page.locator('#confirmYes').click()
        expect(page.locator('#candidateSection')).to_be_visible()
        record('first_pass_hidden_until_confirmation_and_cancel_preserves_it')
        page.locator('.candidate').nth(0).get_by_role('button',name='相关',exact=True).click()
        page.locator('.candidate').nth(1).get_by_role('button',name='不确定',exact=True).click()
        page.locator('#taxonomySummary').click()
        page.locator('#component').select_option('pump')
        page.locator('#intent').select_option('inspection')
        page.locator('#pairNote').fill('仅测试：完整目录查漏')
        page.get_by_role('button',name='添加配对',exact=True).click()
        page.get_by_role('button',name='添加配对',exact=True).click()
        expect(page.locator('#missingPairs .pairItem')).to_have_count(1)
        expect(page.locator('#message')).to_contain_text('已存在')
        page.locator('#coverage').check()
        page.locator('#note').fill('仅测试：甲的中文原始备注，不属于正式专家答案。')
        saved(page)
        page.get_by_role('button',name='保存',exact=True).click();saved(page)
        expect(page.locator('#sourceList').get_by_role('button',name='DEMO001 · 已审核',exact=True)).to_be_visible()
        snapshot(page,'02-review-a.png')
        backup_a=export(page,'导出备份','A.review.json')
        csv_path=export(page,'导出 CSV','A.csv')
        content=csv_path.read_text(encoding='utf-8-sig')
        assert '池外补漏,pump,inspection,相关,仅测试：完整目录查漏' in content
        assert '不确定' in content and '未答' in content and '中文原始备注' in content
        assert json.loads(backup_a.read_text(encoding='utf-8'))['task']['package']['kind']=='practice'
        record('autosave_manual_save_full_taxonomy_missing_pair_csv_and_backup')
        b=create(page,'隔离测试乙')
        assert a['id']!=b['id']
        expect(page.locator('#note')).to_have_value('')
        expect(page.locator('#candidateSection')).not_to_be_visible()
        expect(page.locator('#initialPairs')).to_contain_text('暂无')
        expect(page.locator('#missingPairs')).to_contain_text('暂无')
        backup_b=export(page,'导出备份','B.review.json')
        record('second_expert_gets_no_first_expert_answers')
        snapshot(page,'03-isolated-b.png')
        delayed_checks=[]
        def delayed_open(route):
            assert page.locator('#workspace').evaluate('(el)=>el.inert')
            before=page.locator('#note').input_value()
            page.keyboard.type('SHOULD_NOT_EDIT')
            assert page.locator('#note').input_value()==before
            delayed_checks.append(True)
            route.fulfill(response=route.fetch())
        page.route('**/api/open',delayed_open)
        open_file(page,backup_a)
        expect(page.locator('#taskLabel')).to_contain_text('隔离测试甲')
        expect(page.locator('#note')).to_have_value('仅测试：甲的中文原始备注，不属于正式专家答案。')
        page.unroute('**/api/open',delayed_open)
        assert delayed_checks
        record('opening_old_review_locks_workspace_until_response')
        record('open_old_review_restores_own_answers')
        with page.expect_file_chooser() as chooser:page.get_by_role('button',name='打开旧审查',exact=True).click()
        chooser.value.set_files([])
        expect(page.locator('#taskLabel')).to_contain_text('隔离测试甲')
        bad=RUN/'broken.review.json';bad.write_text('{broken',encoding='utf-8')
        open_file(page,bad)
        expect(page.locator('#message')).to_contain_text('打开失败')
        expect(page.locator('#taskLabel')).to_contain_text('隔离测试甲')
        bad_data=json.loads(backup_a.read_text(encoding='utf-8'));bad_data['task']['reviewer']='被篡改'
        bad.write_text(json.dumps(bad_data,ensure_ascii=False),encoding='utf-8')
        open_file(page,bad)
        expect(page.locator('#message')).to_contain_text('备份校验失败')
        expect(page.locator('#taskLabel')).to_contain_text('隔离测试甲')
        record('cancel_open_and_corrupt_backups_keep_current_review_unchanged')
        snapshot(page,'04-corrupt-backup-protection.png')
        # Force an unavailable save endpoint, then exercise browser beforeunload protection.
        page.route('**/api/save',lambda route:route.abort())
        page.locator('#note').fill('仅测试：关闭前尚未写盘的中文备注')
        expect(page.locator('#message')).to_contain_text('保存未完成',timeout=15000)
        expect(page.locator('#draftBtn')).to_be_visible()
        with page.expect_event('dialog') as warning:page.close(run_before_unload=True)
        warning.value.dismiss()
        assert not page.is_closed()
        record('unsaved_close_warns_and_cancel_keeps_page')
        export(page,'导出待保存副本','unsaved.review.json')
        snapshot(page,'05-unsaved-protection.png')
        context.close()
        stop_server();start_server()
        context=p.chromium.launch_persistent_context(str(PROFILE),channel='msedge',headless=False,viewport={'width':1440,'height':1000},accept_downloads=True)
        page=context.pages[0];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL)
        expect(page.locator('#note')).to_have_value('仅测试：关闭前尚未写盘的中文备注')
        saved(page)
        record('browser_and_server_restart_recovers_pending_chinese_draft')
        backup_latest=export(page,'导出备份','A-latest.review.json')
        # Corrupt only the disposable practice task on disk, then verify browser import recovery.
        (DATA/(a['id']+'.json')).write_text('{broken-local-file',encoding='utf-8')
        open_file(page,backup_latest)
        expect(page.locator('#confirmDialog')).to_be_visible()
        page.locator('#confirmNo').click()
        expect(page.locator('#taskLabel')).to_contain_text('隔离测试甲')
        restore_responses=[]
        def lose_restore_response(route):
            if route.request.post_data_json.get('restore'):
                response=route.fetch()
                assert response.ok
                restore_responses.append(response.json()['task']['id'])
                route.abort()
            else:route.continue_()
        page.route('**/api/open',lose_restore_response)
        open_file(page,backup_latest)
        page.locator('#confirmYes').click()
        expect(page.locator('#message')).to_contain_text('打开失败')
        assert len(restore_responses)==1
        page.unroute('**/api/open',lose_restore_response)
        open_file(page,backup_latest)
        page.locator('#confirmYes').click()
        expect(page.locator('#message')).to_contain_text('隔离练习')
        saved(page)
        restored_path=export(page,'导出备份','A-restored.review.json')
        restored=json.loads(restored_path.read_text(encoding='utf-8'))['task']
        assert restored['id']==restore_responses[0]
        assert restored['id']!=a['id'] and restored['restored_from']['id']==a['id']
        assert (DATA/(a['id']+'.json')).read_text()=='{broken-local-file'
        expect(page.locator('#note')).to_have_value('仅测试：关闭前尚未写盘的中文备注')
        record('damaged_local_record_recovered_as_new_copy_original_preserved')
        record('lost_restore_response_retry_reuses_same_copy')
        snapshot(page,'06-recovered-copy.png')
        page.set_viewport_size({'width':850,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        snapshot(page,'07-narrow-layout.png')
        record('narrow_layout_has_no_horizontal_overflow')
        page.get_by_role('button',name='离开审查',exact=True).click()
        page.locator('#confirmYes').click()
        expect(page.locator('#welcome')).to_be_visible()
        page.reload()
        expect(page.locator('#welcome')).to_be_visible()
        record('leave_clears_resume_entry_for_next_expert')
        assert not errors, errors
        record('no_browser_javascript_errors')
        context.close()
    (RUN/'results.json').write_text(json.dumps({'checks':checks,'page_errors':errors,'practice_only':True,'browser':'Microsoft Edge headed','app':str(APP)},ensure_ascii=False,indent=2),encoding='utf-8')
    print('ARTIFACTS '+str(RUN),flush=True)
finally:
    stop_server()
    (OUT/'latest-run.txt').write_text(str(RUN),encoding='utf-8')
