import unittest,json,copy
from pathlib import Path
from sampler_v4 import readiness,select_formal,NotReady,anchor_quality,original_composite_stratum

class SamplerTests(unittest.TestCase):
    def setUp(self):
        self.draft=json.loads(Path(__file__).with_name('sampling_policy_draft.json').read_text(encoding='utf8'))
        # Synthetic fixture resolution only. Never written to or applied to the real policy/data.
        self.policy=copy.deepcopy(self.draft);self.policy['finalized']=True
        self.policy['raw_support_to_stratum'].update(partial='uncertain',partial_support='uncertain',insufficient='not_supported')
        self.rows=[{'review_id':f'id-{i:03d}','slot':f'slot-{i:03d}','row_index':1,'group':['semantic_new','random_new'][i%2],'review_status':'completed','machine_judgment':{'review_id':f'id-{i:03d}','support':['direct','contradicted','uncertain'][i%3],'applicability':'unknown'},'quality_flags':{'anchor_status':'pass'}} for i in range(441)]
        self.ids=[r['review_id'] for r in self.rows]
    def test_draft_blocks_even_complete_population(self):
        with self.assertRaisesRegex(NotReady,'policy_not_finalized'):select_formal(self.rows,self.ids,self.draft)
    def test_unresolved_partial_blocks(self):
        self.policy['raw_support_to_stratum']['partial']=None
        with self.assertRaisesRegex(NotReady,'unresolved'):select_formal(self.rows,self.ids,self.policy)
    def test_77_success_cannot_generate_formal_sample(self):
        for r in self.rows[77:]:r['review_status']='not_sent';r['machine_judgment']=None
        status=readiness(self.rows,self.ids,self.policy);self.assertEqual(status['completed'],77);self.assertEqual(status['incomplete'],364)
        with self.assertRaises(NotReady):select_formal(self.rows,self.ids,self.policy)
    def test_failed_record_blocks(self):
        self.rows[0]['review_status']='failed_stop'
        with self.assertRaisesRegex(NotReady,'all_441'):select_formal(self.rows,self.ids,self.policy)
    def test_missing_record_blocks(self):
        with self.assertRaisesRegex(NotReady,'population_mismatch'):select_formal(self.rows[:-1],self.ids,self.policy)
    def test_duplicate_ids_blocks(self):
        self.rows[-1]['review_id']=self.rows[0]['review_id']
        with self.assertRaisesRegex(NotReady,'duplicate_review'):select_formal(self.rows,self.ids,self.policy)
    def test_wrong_judgment_id_blocks(self):
        self.rows[0]['machine_judgment']['review_id']='wrong'
        with self.assertRaisesRegex(NotReady,'judgment_id'):select_formal(self.rows,self.ids,self.policy)
    def test_unknown_label_not_silently_bucketed(self):
        self.rows[0]['machine_judgment']['support']='unrecognized'
        with self.assertRaisesRegex(NotReady,'unknown_raw'):select_formal(self.rows,self.ids,self.policy)
    def test_anchor_flags_cannot_change_selection(self):
        a=select_formal(self.rows,self.ids,self.policy)
        for r in self.rows:r['quality_flags']['anchor_status']='fail';r['anchor_and_enum_checks_pass']=False
        b=select_formal(self.rows,self.ids,self.policy)
        self.assertEqual([r['review_id'] for r in a],[r['review_id'] for r in b])
        self.assertTrue(all(r['quality_flags']['anchor_status']=='fail' for r in b))
    def test_applicability_cannot_change_support_stratum(self):
        a=select_formal(self.rows,self.ids,self.policy)
        for r in self.rows:r['machine_judgment']['applicability']='explicit_mismatch'
        b=select_formal(self.rows,self.ids,self.policy);self.assertEqual([r['review_id'] for r in a],[r['review_id'] for r in b])
    def test_no_input_mutation(self):
        before=copy.deepcopy(self.rows);select_formal(self.rows,self.ids,self.policy);self.assertEqual(before,self.rows)
    def test_30_distinct_and_stable_order(self):
        a=select_formal(self.rows,self.ids,self.policy);b=select_formal(list(reversed(self.rows)),self.ids,self.policy)
        self.assertEqual(len(a),30);self.assertEqual(len({r['review_id'] for r in a}),30);self.assertEqual([r['review_id'] for r in a],[r['review_id'] for r in b])
    def test_quality_policy_switch_rejected(self):
        self.policy['quality_flags_affect_stratum']=True
        with self.assertRaisesRegex(NotReady,'must_not_redefine'):select_formal(self.rows,self.ids,self.policy)
    def test_duplicate_positions_rejected(self):
        self.rows[-1]['slot']=self.rows[0]['slot']
        with self.assertRaisesRegex(NotReady,'duplicate_candidate'):select_formal(self.rows,self.ids,self.policy)
    def test_anchor_diagnostic_preserves_support(self):
        j={'support':'direct','anchors':[{'evidence_id':'E1','exact_quote':'not in excerpt'}]};before=copy.deepcopy(j)
        self.assertEqual(anchor_quality(j,{'E1':'original text'})['status'],'fail');self.assertEqual(j,before)
    def test_absent_anchor_unavailable_not_negative(self):self.assertEqual(anchor_quality({'support':'direct'}, {})['status'],'unavailable')
    def test_matching_anchor_pass(self):self.assertEqual(anchor_quality({'anchors':[{'evidence_id':'E1','exact_quote':'alarm'}]}, {'E1':'raise alarm'})['status'],'pass')
    def test_legacy_partial_rule_is_composite_not_support_only(self):
        r={'machine_judgment':{'support':'partial','faithfulness':'faithful_paraphrase'}};self.assertEqual(original_composite_stratum(r),'other_uncertain_error')
        r['machine_judgment']['faithfulness']='new_inference_or_synthesis';self.assertEqual(original_composite_stratum(r),'explicit_negative')
    def test_legacy_diagnostic_ignores_anchor_flag(self):
        r={'machine_judgment':{'support':'direct','applicability':'explicit_match'},'anchor_and_enum_checks_pass':False};self.assertEqual(original_composite_stratum(r),'direct_and_applicable')
    def test_population_size_not_redefined(self):
        self.policy['required_review_population']=77
        with self.assertRaisesRegex(NotReady,'population_must'):select_formal(self.rows,self.ids,self.policy)

if __name__=='__main__':unittest.main()
