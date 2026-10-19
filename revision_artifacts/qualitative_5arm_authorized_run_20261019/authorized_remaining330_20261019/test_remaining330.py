import unittest
from decimal import Decimal
import resume330 as r
from test_resume import RunnerTests,ReviewRunnerTests,IdentityTests

class RemainingTests(unittest.TestCase):
    def setUp(self):
        self.items=r.t.read(r.WORK/'QWEN_FROZEN_PLAN.json')['requests']
        self.a=[r.t.read(p) for p in sorted((r.PREVIOUS/'review').glob('*_attempt.json'))]
        self.responses=[r.t.read(p) for p in sorted((r.PREVIOUS/'review').glob('*_response.json'))]
    def reconcile(self):return r.reconcile(self.items,self.a,self.responses,'10.1052076')
    def test_exact_suffix_no_success_or_quarantine(self):
        pending,debit=self.reconcile();self.assertEqual(pending,self.items[111:]);self.assertEqual(len(pending),330);self.assertEqual(debit,Decimal('10.4038132'))
        self.assertFalse({x['review_id'] for x in pending}&{x['review_id'] for x in self.items[:111]})
    def test_quarantined_cannot_become_success(self):
        self.responses[-1]['status']='completed';self.responses[-1]['parsed']={'review_id':self.items[110]['review_id']};self.responses[-1]['usage_cost_CNY']='0.0081336'
        with self.assertRaises(ValueError):self.reconcile()
    def test_missing_record_blocks(self):
        self.responses.pop()
        with self.assertRaises(ValueError):self.reconcile()
    def test_other_failure_blocks(self):
        self.responses[-1]['error']='HTTP_500'
        with self.assertRaises(ValueError):self.reconcile()
    def test_request_drift_blocks(self):
        self.a[-1]['body_sha256']='changed'
        with self.assertRaises(ValueError):self.reconcile()
    def test_duplicate_frozen_candidate_blocks(self):
        self.items[-1]=self.items[0]
        with self.assertRaises(ValueError):self.reconcile()
    def test_existing_responses_unchanged(self):
        before=[r.t.digest(x) for x in self.responses];self.reconcile();self.assertEqual(before,[r.t.digest(x) for x in self.responses])

if __name__=='__main__':unittest.main()
