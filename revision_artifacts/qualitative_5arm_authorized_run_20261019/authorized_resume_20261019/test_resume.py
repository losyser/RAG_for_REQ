import copy
import sys
import unittest
from decimal import Decimal
import resume
import transport
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import test_runner
import test_review_runner
test_runner.r=transport
test_review_runner.r=transport
from test_runner import RunnerTests
from test_review_runner import ReviewRunnerTests

class ContinuationTests(unittest.TestCase):
    def setUp(self):
        w=resume.WORK
        self.items=transport.read(w/'QWEN_FROZEN_PLAN.json')['requests']
        self.a=[transport.read(p) for p in sorted((w/'review').glob('*_attempt.json'))]
        self.r=[transport.read(p) for p in sorted((w/'review').glob('*_response.json'))]
        self.prior=transport.read(w/'generation/state.json')['debit_CNY']
    def test_exact_scope_and_failed_reservation(self):
        pending,debit=resume.reconcile(self.items,self.a,self.r,self.prior)
        self.assertEqual(pending,self.items[77:]);self.assertEqual(len(pending),364)
        self.assertEqual(debit,Decimal('10.1052076'))
        self.assertFalse(set(x['review_id'] for x in pending)&set(x['review_id'] for x in self.items[:77]))
    def test_original_request_tamper_blocks(self):
        self.a[77]['body_sha256']='changed'
        with self.assertRaises(ValueError):resume.reconcile(self.items,self.a,self.r,self.prior)
    def test_duplicate_frozen_id_blocks(self):
        self.items[-1]=self.items[0]
        with self.assertRaises(ValueError):resume.reconcile(self.items,self.a,self.r,self.prior)
    def test_unknown_failure_blocks(self):
        self.r[77]['raw_response_body']='other failure'
        with self.assertRaises(ValueError):resume.reconcile(self.items,self.a,self.r,self.prior)
    def test_missing_old_attempt_blocks(self):
        with self.assertRaises(ValueError):resume.reconcile(self.items,self.a[:-1],self.r,self.prior)
    def test_prior_success_wrong_id_blocks(self):
        self.r[0]['parsed']['review_id']='wrong'
        with self.assertRaises(ValueError):resume.reconcile(self.items,self.a,self.r,self.prior)

class IdentityTests(test_review_runner.ReviewRunnerTests):
    def test_baseline_identity_checked_on_first_new_attempt(self):
        from unittest.mock import Mock
        response=Mock(status_code=200,headers={},text='raw preserved')
        response.json.return_value=self.payload
        self.client.post.return_value=response
        state=transport.Engine(self.folder,'review',[self.item],self.client,'mock-secret',prior_debit='10',baseline_identity={'model':'qwen-max','system_fingerprint':'old'}).run()
        self.assertEqual(state['status'],'paused_failure')
        self.assertEqual(self.client.post.call_count,1)
        self.assertEqual(Decimal(state['debit_CNY']),Decimal('10.0933888'))
        self.assertEqual(transport.read(self.folder/'0001_response.json')['raw_response_body'],'raw preserved')

if __name__=='__main__':unittest.main()
