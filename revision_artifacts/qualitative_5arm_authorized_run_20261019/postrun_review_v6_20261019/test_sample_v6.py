import copy,json,unittest
from pathlib import Path
from sample_v6 import select

class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.p=json.loads((Path(__file__).parent/'outputs/01a13537-v6/02_仅协调者_勿发盲审者/协议修订_v6.json').read_text(encoding='utf8'))
        self.rows=[{'review_id':str(i),'slot':str(i),'row_index':1,'group':self.p['groups'][i%2],'review_status':'completed','machine_judgment':{'review_id':str(i),'support':self.p['labels'][(i//2)%5],'applicability':'unknown'},'anchor_quality':{'status':'fail'}} for i in range(440)]
        self.ids=[r['review_id'] for r in self.rows]
    def run_sample(self):return select(self.rows,self.ids,self.p)
    def test_balanced_three_per_stratum(self):
        out,strata=self.run_sample();self.assertEqual(len(out),30);self.assertEqual([x['selected'] for x in strata],[3]*10)
    def test_probabilities(self):
        _,strata=self.run_sample()
        for s in strata:self.assertEqual(s['nominal_inclusion_fraction'],s['selected']/s['population'])
    def test_order_independence(self):
        expected=self.run_sample();self.rows.reverse();self.assertEqual(expected,self.run_sample())
    def test_no_mutation(self):
        before=copy.deepcopy(self.rows);self.run_sample();self.assertEqual(before,self.rows)
    def test_anchor_applicability_do_not_select(self):
        ids=[r['review_id'] for r in self.run_sample()[0]]
        for r in self.rows:r['anchor_quality']['status']='pass';r['machine_judgment']['applicability']='explicit_match'
        self.assertEqual(ids,[r['review_id'] for r in self.run_sample()[0]])
    def test_empty_strata_redistribute(self):
        for r in self.rows:r['machine_judgment']['support']='partial'
        out,strata=self.run_sample();self.assertEqual(len(out),30);self.assertEqual([s['selected'] for s in strata if s['population']],[15,15])
    def test_partial_support_unexpected(self):
        self.rows[0]['machine_judgment']['support']='partial_support'
        with self.assertRaises(ValueError):self.run_sample()
    def test_incomplete_blocked(self):
        self.rows[0]['review_status']='not_sent'
        with self.assertRaises(ValueError):self.run_sample()
    def test_duplicate_blocked(self):
        self.rows[0]=self.rows[1]
        with self.assertRaises(ValueError):self.run_sample()
    def test_wrong_id_blocked(self):
        self.rows[0]['machine_judgment']['review_id']='wrong'
        with self.assertRaises(ValueError):self.run_sample()
    def test_changed_seed_blocked(self):
        self.p['hash_salt']='new'
        with self.assertRaises(ValueError):self.run_sample()
    def test_small_strata(self):
        for r in self.rows:r['machine_judgment']['support']='direct'
        self.rows[0]['machine_judgment']['support']='partial'
        out,strata=self.run_sample();self.assertEqual(len(out),30);self.assertEqual(next(s for s in strata if s['group']=='semantic_new' and s['raw_support']=='partial')['selected'],1)

if __name__=='__main__':unittest.main()
