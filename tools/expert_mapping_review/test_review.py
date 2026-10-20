import importlib.util
import pathlib
import tempfile
import unittest
import copy
import json
import threading
import urllib.request
import urllib.error

spec = importlib.util.spec_from_file_location('review', pathlib.Path(__file__).with_name('server.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

class ReviewTests(unittest.TestCase):
    def test_independent_tasks_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = review.Store(pathlib.Path(tmp))
            a = store.create('专家甲', review.demo_package(), 'a' * 32)
            b = store.create('专家乙', review.demo_package(), 'b' * 32)
            self.assertNotEqual(a['task']['id'], b['task']['id'])
            state = a['task']['answers']
            state['DEMO001']['note'] = '中文独立原始记录'
            store.save(a['task']['id'], a['token'], 0, state, 0)
            reopened = review.Store(pathlib.Path(tmp)).get(a['task']['id'], a['token'])
            self.assertEqual(reopened['answers']['DEMO001']['note'], '中文独立原始记录')
            self.assertEqual(store.get(b['task']['id'], b['token'])['answers']['DEMO001']['note'], '')
            with self.assertRaises(review.ReviewError):
                store.get(a['task']['id'], b['token'])

    def test_idempotent_create_and_stale_save_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = review.Store(pathlib.Path(tmp))
            a = store.create('甲', review.demo_package(), 'a' * 32)
            again = store.create('甲', review.demo_package(), 'a' * 32)
            self.assertEqual(a, again)
            store.save(a['task']['id'], a['token'], 0, a['task']['answers'], 0)
            with self.assertRaises(review.ReviewError):
                store.save(a['task']['id'], a['token'], 0, a['task']['answers'], 0)

    def test_missing_pairs_export_and_frozen_first_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = review.Store(pathlib.Path(tmp)); a = store.create('甲', review.demo_package(), 'a' * 32)
            answers = a['task']['answers']; first = answers['DEMO001']
            first['initial_pairs'] = [{'component':'pump','intent':'inspection','verdict':'relevant','note':'中文首判'}]
            first['first_pass_done'] = True
            store.save(a['task']['id'], a['token'], 0, answers, 0)
            first['candidates']['pump:redundancy'] = 'relevant'
            first['candidates']['sensor:alarm'] = 'uncertain'
            first['missing_pairs'] = [{'component':'pump','intent':'inspection','verdict':'relevant','note':'遗漏检查'}]
            first['coverage_reviewed'] = True
            task = store.save(a['task']['id'], a['token'], 1, answers, 0)
            report = review.csv_export(task).decode('utf-8-sig')
            self.assertIn('池外补漏,pump,inspection,相关,遗漏检查', report)
            self.assertIn('不确定', report)
            self.assertIn('未答', report)
            self.assertFalse(review.summary(task)['gold_ready'])
            first['initial_pairs'] = []
            with self.assertRaises(review.ReviewError): store.save(task['id'], a['token'], 2, answers, 0)

    def test_invalid_backup_and_corrupt_store_never_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = review.Store(pathlib.Path(tmp)); a = store.create('甲', review.demo_package(), 'a' * 32)
            backup = store.backup(a['task']['id'], a['token'])
            damaged = copy.deepcopy(backup); damaged['task']['reviewer'] = '被更改'
            with self.assertRaises(review.ReviewError): store.open_backup(damaged)
            path = pathlib.Path(tmp) / (a['task']['id'] + '.json')
            path.write_text('{broken', encoding='utf-8')
            with self.assertRaises(review.ReviewError): store.save(a['task']['id'], a['token'], 0, a['task']['answers'], 0)
            self.assertEqual(path.read_text(), '{broken')
            restored = store.open_backup(backup, True, 'c' * 32)
            self.assertNotEqual(restored['task']['id'], a['task']['id'])
            self.assertEqual(restored['task']['restored_from']['id'], a['task']['id'])
            self.assertEqual(path.read_text(), '{broken')

    def test_incomplete_invalid_and_duplicate_pairs_are_not_gold(self):
        package = review.demo_package(); answers = review.blank_answers(package)
        self.assertEqual(answers['DEMO001']['candidates']['pump:redundancy'], 'unanswered')
        answers['DEMO001']['first_pass_done'] = True
        answers['DEMO001']['missing_pairs'] = [{'component':'pump','intent':'alarm','verdict':'relevant','note':''}]
        with self.assertRaises(review.ReviewError): review.validate_answers(package, answers)
        answers['DEMO001']['missing_pairs'][0]['intent'] = 'redundancy'
        with self.assertRaises(review.ReviewError): review.validate_answers(package, answers)

    def test_loopback_http_whitelist_and_task_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = review.Server(0, tmp)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            base = 'http://127.0.0.1:' + str(server.server_port)
            try:
                def post(path, body, headers=None):
                    req = urllib.request.Request(base+path, data=json.dumps(body).encode(), headers={'Content-Type':'application/json', **(headers or {})})
                    return json.load(urllib.request.urlopen(req))
                a = post('/api/new', {'kind':'practice','reviewer':'甲','request_id':'a'*32})
                self.assertNotIn('token_hash', json.dumps(a))
                self.assertNotIn('expert_key', json.dumps(a))
                for path in ['/api/tasks', '/expert_key.json', '/../server.py', '/local_records/'+a['task']['id']+'.json']:
                    with self.assertRaises(urllib.error.HTTPError) as caught: urllib.request.urlopen(base+path)
                    caught.exception.close()
                with self.assertRaises(urllib.error.HTTPError) as caught: post('/api/get', {'id':a['task']['id'],'token':'wrong'})
                caught.exception.close()
                with self.assertRaises(urllib.error.HTTPError) as caught: post('/api/get', {'id':a['task']['id'],'token':a['token']}, {'Origin':'https://example.com'})
                caught.exception.close()
            finally: server.shutdown();server.server_close();thread.join()

    def test_assignment_preparation_with_synthetic_files_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/'cooling_rag_mg').mkdir()
            (root/'data/search_results/exp_v4').mkdir(parents=True)
            (root/'cooling_rag_mg/evidence_taxonomy.py').write_text("COMPONENTS: dict = {'pump':'练习泵'}\nINTENTS: dict = {'inspection':'检查'}\nTAXONOMY: dict = {'pump':['inspection']}\nraise RuntimeError('Must never execute this module')\n",encoding='utf-8')
            (root/'data/search_results/exp_v4/e1_pool.csv').write_text('or_id,requirement_text,component,intent\nTEST001,人工构造的单元测试需求,pump,inspection\n',encoding='utf-8')
            output=root/'synthetic.assignment.json'
            review.prepare_assignment(root,'TEST001','synthetic-test-only',output)
            package=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(package['sources'][0]['text'],'人工构造的单元测试需求')
            self.assertNotIn('answers',package)
            self.assertEqual(package['provenance']['prediction_scope'],'historical-upstream-stage1-used-by-v4; stored-in-v3; no-new-run')
            with self.assertRaises(FileExistsError): review.prepare_assignment(root,'TEST001','synthetic-test-only',output)

    def test_pilot_is_distinct_and_private_fields_rejected(self):
        package=review.demo_package()
        package['kind']='pilot'
        package['protocol']='timing-calibration-exclude-from-formal'
        package['version']=review.digest({k:v for k,v in package.items() if k!='version'})
        review.validate_package(package)
        with tempfile.TemporaryDirectory() as tmp:
            a=review.Store(pathlib.Path(tmp)).create('测试',package,'d'*32)
            self.assertEqual(a['task']['package']['kind'],'pilot')
            self.assertIn('pilot',review.csv_export(a['task']).decode('utf8'))
            for answer in a['task']['answers'].values():
                answer['first_pass_done']=True;answer['coverage_reviewed']=True
                answer['candidates']={key:'irrelevant' for key in answer['candidates']}
            self.assertFalse(review.summary(a['task'])['gold_ready'])
        for field in ('expert_key','PRIVATE','predictions','model_labels','gold'):
            contaminated=copy.deepcopy(package);contaminated[field]={}
            contaminated['version']=review.digest({k:v for k,v in contaminated.items() if k!='version'})
            with self.assertRaises(review.ReviewError):review.validate_package(contaminated)

    def test_converter_preserves_legal_intent_missing_dictionary_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/'cooling_rag_mg').mkdir()
            (root/'data/search_results/exp_v4').mkdir(parents=True)
            (root/'cooling_rag_mg/evidence_taxonomy.py').write_text("COMPONENTS: dict = {'pump':'泵'}\nINTENTS: dict = {'inspection':'检查'}\nTAXONOMY: dict = {'pump':[\n 'missing', # 原始说明\n 'inspection'\n]}\nraise RuntimeError('Do not execute')\n",encoding='utf8')
            (root/'data/search_results/exp_v4/e1_pool.csv').write_text('or_id,requirement_text,component,intent\nTEST001,测试,pump,missing\n',encoding='utf8')
            package=review.build_assignment(root,'TEST001','test','pilot')
            self.assertEqual(package['taxonomy']['pump'],['missing','inspection'])
            self.assertEqual(package['intents']['missing'],'[原目录行注释] 原始说明')
            with self.assertRaises(review.ReviewError):review.build_assignment(root,'UNKNOWN','test','pilot')
            with self.assertRaises(review.ReviewError):review.build_assignment(root,'TEST001,TEST001','test','pilot')

if __name__ == '__main__':
    unittest.main()
