"""Synthetic labels only, in memory or temporary files; never edits expert materials."""
import copy,json,tempfile,unittest
from pathlib import Path
import score_formal_review as scorer

class FormalScoreTests(unittest.TestCase):
    def setUp(self):
        self.pkg={'schema':1,'kind':'formal','title':'SYNTHETIC TEST ONLY','protocol':'synthetic-test-v1',
            'provenance':{'source_sha256':'synthetic','taxonomy_sha256':'synthetic','prediction_scope':'synthetic fixture, not research'},
            'components':{'pump':'测试部件'},'intents':{'good':'相关','bad':'不相关','missed':'池外相关'},
            'taxonomy':{'pump':['good','bad','missed']},'sources':[]}
        for i in range(8):
            self.pkg['sources'].append({'id':f'SYN{i}','text':'SYNTHETIC TEXT',
                'candidates':[{'id':'pump:'+v,'component':'pump','intent':v} for v in ('good','bad')]})
        self.pkg['version']=scorer.review.digest(self.pkg)
        self.man={'n':8,'selected_source_ids':[s['id'] for s in self.pkg['sources']],'package_version':self.pkg['version'],'predictions_sha256':'synthetic'}
        self.pred={method:{s['id']:[['pump',v] for v in intents] for s in self.pkg['sources']} for method,intents in
                   [('deepseek',['good']),('qwen',['bad']),('bm25',['good','bad']),('embed',[])]}
        answers=scorer.review.blank_answers(self.pkg)
        for a in answers.values():
            a.update(first_pass_done=True,coverage_reviewed=True,candidates={'pump:good':'relevant','pump:bad':'irrelevant'})
            a['initial_pairs']=[{'component':'pump','intent':'good','verdict':'relevant','note':'SYNTHETIC'}]
            a['missing_pairs']=[{'component':'pump','intent':'missed','verdict':'relevant','note':'SYNTHETIC'}]
            a['review_details'].update(exposure='after_first_pass',first_pass_at='2026-10-17T10:00:00Z',first_candidate_at='2026-10-17T10:01:00Z',total_minutes=10,interruption_minutes=0,complete='yes')
        self.record={'kind':'formal','package_version':self.pkg['version'],'reviewer':'SYNTHETIC_A','collection_mode':'web','web_answer_fields':answers,'issues':[],'pending_pair_rows':[]}
    def runscore(self,records=None,n=1):return scorer.score(self.pkg,self.man,self.pred,records or [self.record],n)
    def blocked(self):
        r=self.runscore();self.assertEqual(r['status'],'blocked');self.assertIsNone(r['scores']);self.assertEqual(len(r['source_ids']),8);return r
    def test_complete_known_counts_and_missing_pool_recall(self):
        r=self.runscore();self.assertEqual(r['status'],'scored')
        for method,counts in [('deepseek',(8,0,8)),('qwen',(0,8,16)),('bm25',(8,8,8)),('embed',(0,0,16))]:
            m=r['scores'][method]['micro'];self.assertEqual((m['tp'],m['fp'],m['fn']),counts)
            self.assertEqual(len(r['scores'][method]['per_source']),8)
        self.assertAlmostEqual(r['scores']['deepseek']['micro']['f1'],2/3)
        self.assertEqual(r['scores']['bm25']['micro']['f1'],.5)
        self.assertIsNone(r['scores']['embed']['micro']['precision'])
        self.assertIsNone(r['inter_reviewer_agreement'])
        self.assertEqual(r['coverage'][0]['definitive_candidate_fraction'],1)
    def test_unanswered_blocks_all_not_complete_case(self):
        self.record['web_answer_fields']['SYN0']['candidates']['pump:good']='unanswered'
        r=self.blocked();self.assertEqual(r['coverage'][0]['definitive_candidate_fraction'],15/16)
    def test_uncertain_candidate_never_negative(self):
        self.record['web_answer_fields']['SYN0']['candidates']['pump:good']='uncertain';self.blocked()
    def test_uncertain_missing_pair_blocks(self):
        self.record['web_answer_fields']['SYN0']['missing_pairs'][0]['verdict']='uncertain';self.blocked()
    def test_missing_source_blocks(self):
        del self.record['web_answer_fields']['SYN0'];self.blocked()
    def test_full_taxonomy_not_reviewed_blocks(self):
        self.record['web_answer_fields']['SYN0']['coverage_reviewed']=False;self.blocked()
    def test_unfinished_declaration_blocks(self):
        self.record['web_answer_fields']['SYN0']['review_details']['complete']='no';self.blocked()
    def test_early_candidate_exposure_blocks(self):
        self.record['web_answer_fields']['SYN0']['review_details']['exposure']='before_first_pass';self.blocked()
    def test_legacy_web_missing_metadata_blocks_not_invented(self):
        del self.record['web_answer_fields']['SYN0']['review_details'];self.blocked()
    def test_missing_timing_blocks(self):
        self.record['web_answer_fields']['SYN0']['review_details']['total_minutes']=None;self.blocked()
    def test_invalid_timing_blocks(self):
        self.record['web_answer_fields']['SYN0']['review_details']['total_minutes']=-1;self.blocked()
    def test_open_question_blocks(self):
        self.record['web_answer_fields']['SYN0']['review_details']['questions']='SYNTHETIC unresolved';self.blocked()
    def test_wrong_record_version_blocks(self):
        self.record['package_version']='wrong';self.blocked()
    def test_wrong_manifest_version_rejected(self):
        self.man['package_version']='wrong'
        with self.assertRaises(ValueError):self.runscore()
    def test_duplicate_missing_pair_blocks(self):
        a=self.record['web_answer_fields']['SYN0'];a['missing_pairs']*=2;self.blocked()
    def test_duplicate_source_in_package_rejected(self):
        self.pkg['sources'][1]['id']='SYN0';self.pkg['version']=scorer.review.digest({k:v for k,v in self.pkg.items() if k!='version'})
        with self.assertRaises(scorer.review.ReviewError):self.runscore()
    def test_duplicate_json_source_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'synthetic.json';p.write_text('{"SYN0":{},"SYN0":{}}')
            with self.assertRaises(ValueError):scorer.strict_json(p)
    def test_duplicate_prediction_pair_rejected(self):
        self.pred['deepseek']['SYN0']*=2
        with self.assertRaises(ValueError):self.runscore()
    def test_two_reviewers_conflict_blocks(self):
        b=copy.deepcopy(self.record);b['reviewer']='SYNTHETIC_B';b['web_answer_fields']['SYN0']['candidates']['pump:bad']='relevant'
        r=self.runscore([self.record,b],2);self.assertEqual(r['status'],'blocked');self.assertIsNone(r['scores']);self.assertEqual(r['reference_mode'],'reference-not-ready')
    def test_two_reviewers_agree(self):
        b=copy.deepcopy(self.record);b['reviewer']='SYNTHETIC_B'
        self.assertEqual(self.runscore([self.record,b],2)['status'],'scored')
    def test_no_automatic_single_reviewer_fallback(self):
        self.assertEqual(self.runscore([self.record],2)['status'],'blocked')
    def test_duplicate_reviewer_identity_blocks(self):
        b=copy.deepcopy(self.record);b['reviewer']='  SYNTHETIC_A  '
        self.assertEqual(self.runscore([self.record,b],2)['status'],'blocked')
    def test_unresolved_initial_positive_blocks(self):
        self.record['web_answer_fields']['SYN0']['missing_pairs']=[]
        self.record['web_answer_fields']['SYN0']['initial_pairs'].append({'component':'pump','intent':'missed','verdict':'relevant','note':''});self.blocked()
    def test_web_backup_checksum_roundtrip(self):
        b={'format':'mapping-review-backup-v1','task':{'package':self.pkg,'reviewer':'SYNTHETIC_A','answers':self.record['web_answer_fields']},'token':'SYNTHETIC'}
        b['sha256']=scorer.review.digest(b)
        self.assertEqual(self.runscore([scorer.normalize_record(b,self.pkg)])['status'],'scored')
        b['task']['reviewer']='CHANGED'
        with self.assertRaises(ValueError):scorer.normalize_record(b,self.pkg)
    def test_zero_denominators_null_macro_not_silently_omitted(self):
        for a in self.record['web_answer_fields'].values():a.update(initial_pairs=[],missing_pairs=[],note='SYNTHETIC',candidates={'pump:good':'irrelevant','pump:bad':'irrelevant'})
        r=self.runscore();self.assertIsNone(r['scores']['embed']['micro']['f1']);self.assertIsNone(r['scores']['embed']['macro_f1'])

if __name__=='__main__':unittest.main(verbosity=2)
