import tempfile,unittest,json
from pathlib import Path
from unittest.mock import Mock
from decimal import Decimal
import runner as r

class ReviewRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)/'review';self.client=Mock()
        b={'model':'qwen-max','messages':[{'role':'system','content':'frozen review instruction'},{'role':'user','content':'mock candidate'}],'temperature':0,'max_tokens':2048,'response_format':{'type':'json_object'}}
        self.item={'slot':'blind-id','review_id':'blind-id','body':b,'body_sha256':r.digest(b)}
        self.payload={'model':'qwen-max','usage':{'prompt_tokens':100,'completion_tokens':200,'total_tokens':300},'choices':[{'finish_reason':'stop','message':{'content':'{"review_id":"blind-id","support":"uncertain"}'}}]}
    def tearDown(self):self.temp.cleanup()
    def run_engine(self):
        response=Mock();response.status_code=200;response.headers={};response.text=json.dumps(self.payload);response.json.return_value=self.payload;self.client.post.return_value=response
        return r.Engine(self.folder,'review',[self.item],self.client,'mock-secret',prior_debit=Decimal('10')).run()
    def test_exact_Qwen_endpoint(self):
        self.assertEqual(self.run_engine()['status'],'completed');self.assertEqual(self.client.post.call_args.args[0],'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
    def test_review_cost_uses_Qwen_rates(self):self.assertEqual(Decimal(self.run_engine()['debit_CNY']),Decimal('10.00216'))
    def test_uncertain_not_rejected_or_retried(self):
        self.run_engine();self.assertEqual(r.read(self.folder/'0001_response.json')['parsed']['support'],'uncertain');self.assertEqual(self.client.post.call_count,1)
    def test_wrong_candidate_id_stops(self):
        self.payload['choices'][0]['message']['content']='{"review_id":"wrong"}';self.assertEqual(self.run_engine()['status'],'paused_failure')
    def test_output_over2048_stops(self):
        self.payload['usage']={'prompt_tokens':100,'completion_tokens':2049,'total_tokens':2149};self.assertEqual(self.run_engine()['status'],'paused_failure')
    def test_review_cap1200(self):
        with self.assertRaisesRegex(ValueError,'cap'):r.Engine(self.folder,'review',[dict(self.item,slot=str(i)) for i in range(1201)],self.client,'mock-secret')

if __name__=='__main__':unittest.main()
