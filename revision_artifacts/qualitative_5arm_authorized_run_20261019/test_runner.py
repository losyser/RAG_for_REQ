import copy,json,tempfile,unittest
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock
import runner as r

def item(slot='a'):
    b={'model':'deepseek-flash','messages':[{'role':'user','content':'mock only'}],'temperature':0,'max_tokens':8192,'response_format':{'type':'json_object'},'extra_body':{'thinking':{'type':'disabled'}}}
    return {'slot':slot,'body':b,'body_sha256':r.digest(b)}
def payload():return {'model':'deepseek-flash','system_fingerprint':'same','usage':{'prompt_tokens':100,'completion_tokens':200,'total_tokens':300},'choices':[{'finish_reason':'stop','message':{'content':'{"shalls": []}'}}]}
def response(p=None,status=200):
    p=payload() if p is None else p;x=Mock();x.status_code=status;x.text=json.dumps(p);x.headers={'Authorization':'secret-not-log','date':'today'};x.json.return_value=p;return x

class RunnerTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)/'run';self.client=Mock();self.client.post.return_value=response()
    def tearDown(self):self.temp.cleanup()
    def engine(self,items=None,prior=r.PRIOR):return r.Engine(self.folder,'generation',items or [item()],self.client,'sk-test-secret-key-123456',prior_debit=prior)
    def test_reservations(self):self.assertEqual(r.reserve(r.PROVIDERS['generation']),Decimal('2.162688'));self.assertEqual(r.reserve(r.PROVIDERS['review']),Decimal('0.0933888'))
    def test_success_updates_usage_and_redacts_headers(self):
        s=self.engine().run();self.assertEqual(s['status'],'completed');self.assertEqual(Decimal(s['debit_CNY']),r.PRIOR+Decimal('0.0018'));self.assertNotIn('Authorization',r.read(self.folder/'0001_response.json')['response_headers'])
    def test_frozen_wire(self):
        self.engine().run();args,kw=self.client.post.call_args;self.assertEqual(args[0],r.PROVIDERS['generation']['endpoint']);self.assertEqual(kw['json']['thinking'],{'type':'disabled'});self.assertNotIn('extra_body',kw['json'])
    def test_http_failure_stops_remaining(self):
        self.client.post.return_value=response(status=402);s=self.engine([item('a'),item('b')]).run();self.assertEqual(s['status'],'paused_failure');self.assertEqual(self.client.post.call_count,1);self.assertEqual(s['unsent'],1);self.assertEqual(Decimal(s['debit_CNY']),r.PRIOR+Decimal('2.162688'))
    def test_timeout_does_not_retry(self):
        self.client.post.side_effect=TimeoutError('timeout');self.engine([item('a'),item('b')]).run();self.assertEqual(self.client.post.call_count,1)
    def test_failed_resume_refused(self):
        self.client.post.return_value=response(status=500);self.engine().run()
        with self.assertRaisesRegex(RuntimeError,'unresolved'):self.engine().run()
        self.assertEqual(self.client.post.call_count,1)
    def test_success_resume_does_not_repeat(self):
        self.engine().run();self.engine().run();self.assertEqual(self.client.post.call_count,1)
    def test_budget_before_dispatch(self):
        s=self.engine(prior='48').run();self.assertEqual(s['status'],'paused_budget');self.client.post.assert_not_called();self.assertEqual(s['unsent'],1)
    def test_lock_prevents_parallel(self):
        e=self.engine();(self.folder/'RUNNING.lock').write_text('previous')
        with self.assertRaises(FileExistsError):e.run()
        self.client.post.assert_not_called()
    def test_crash_pending_prevents_resend(self):
        e=self.engine();r.exclusive(self.folder/'0001_attempt.json',{'slot':'a','plan_hash':e.plan_hash,'body_sha256':item()['body_sha256'],'reserved_CNY':'2.162688'})
        with self.assertRaisesRegex(RuntimeError,'unresolved'):e.run()
        self.client.post.assert_not_called()
    def test_hash_tamper(self):
        i=item();i['body']['messages'][0]['content']='changed'
        with self.assertRaisesRegex(ValueError,'hash'):self.engine([i])
    def test_parameter_tamper(self):
        i=item();i['body']['max_tokens']=999;i['body_sha256']=r.digest(i['body'])
        with self.assertRaisesRegex(ValueError,'parameter'):self.engine([i])
    def test_extra_tools_rejected(self):
        i=item();i['body']['tools']=[];i['body_sha256']=r.digest(i['body'])
        with self.assertRaisesRegex(ValueError,'extra_request'):self.engine([i])
    def test_duplicate_slots(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):self.engine([item(),item()])
    def test_cap(self):
        with self.assertRaisesRegex(ValueError,'cap'):self.engine([item(str(i)) for i in range(301)])
    def test_missing_usage_retains_full_reserve(self):
        p=payload();p.pop('usage');self.client.post.return_value=response(p);s=self.engine().run();self.assertEqual(s['status'],'paused_failure');self.assertEqual(Decimal(s['debit_CNY']),r.PRIOR+r.reserve(r.PROVIDERS['generation']))
    def test_invalid_usage_boolean(self):
        p=payload();p['usage']['prompt_tokens']=True
        with self.assertRaises(ValueError):r.usage_cost(p,r.PROVIDERS['generation'])
    def test_usage_over_output_limit(self):
        p=payload();p['usage']['completion_tokens']=8193
        with self.assertRaises(ValueError):r.usage_cost(p,r.PROVIDERS['generation'])
    def test_total_mismatch(self):
        p=payload();p['usage']['total_tokens']=1
        with self.assertRaises(ValueError):r.usage_cost(p,r.PROVIDERS['generation'])
    def test_identity_drift_stops(self):
        p=payload();p['system_fingerprint']='changed';self.client.post.side_effect=[response(),response(p),response()]
        s=self.engine([item('a'),item('b'),item('c')]).run();self.assertEqual(s['status'],'paused_failure');self.assertEqual(self.client.post.call_count,2)
    def test_wrong_model(self):
        p=payload();p['model']='other'
        with self.assertRaisesRegex(ValueError,'model'):r.usage_cost(p,r.PROVIDERS['generation'])
    def test_truncation_stops(self):
        p=payload();p['choices'][0]['finish_reason']='length';self.client.post.return_value=response(p);self.assertEqual(self.engine().run()['status'],'paused_failure')
    def test_invalid_json_stops_no_repair(self):
        p=payload();p['choices'][0]['message']['content']='broken';self.client.post.return_value=response(p);self.engine().run();self.assertEqual(self.client.post.call_count,1)
    def test_redaction(self):
        self.assertNotIn('private-key',json.dumps(r.redact({'error':'private-key'},['private-key'])))
    def test_secret_error_not_logged(self):
        self.client.post.side_effect=RuntimeError('sk-test-secret-key-123456');self.engine().run();self.assertNotIn('sk-test-secret-key-123456',(self.folder/'0001_response.json').read_text())
    def test_resume_plan_changed(self):
        self.engine().run()
        with self.assertRaisesRegex(RuntimeError,'plan_mismatch'):self.engine([item('other')]).run()
        self.assertEqual(self.client.post.call_count,1)

if __name__=='__main__':unittest.main()
