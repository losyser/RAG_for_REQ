import json,unittest
from postprocess import blind_packet,evidence_segments,judge_band

class PacketTests(unittest.TestCase):
    def setUp(self):
        self.context={'selected_ids':['REAL1','REAL2'],'evidence_block':'[REAL1] 层级:L1 来源:standard\n  内容:报警时须发出声光信号。\n\n[REAL2] 层级:L2 来源:manual\n  内容:另一个条件。\n'}
        self.item={'slot':'OR001-semantic_new','source_id':'OR001','group':'semantic_new'}
        self.row={'er_id':'OR001.1','_grade':'B','measurable_criterion':'[Q] 报警时须发出声光信号 [REAL1]','applicable_condition':'报警时','evidence_citations':[{'kb_id':'REAL1','tier':'L1','source':'standard'}]}
    def packet(self):return blind_packet(self.item,self.row,1,self.context,'原始需求')
    def test_only_supplied_cited_evidence(self):
        p,k=self.packet();self.assertEqual(len(p['cited_evidence']),1);self.assertIn('声光信号',p['cited_evidence'][0]['supplied_excerpt']);self.assertNotIn('另一个条件',json.dumps(p,ensure_ascii=False))
    def test_masks_label_identifiers(self):
        p,k=self.packet();text=json.dumps(p);self.assertNotIn('OR001',text);self.assertNotIn('semantic_new',text);self.assertNotIn('REAL1',text);self.assertNotIn('_grade',text);self.assertEqual(k['source_id'],'OR001')
    def test_stable_ids(self):self.assertEqual(self.packet()[0]['review_id'],self.packet()[0]['review_id'])
    def test_row_position_distinct(self):self.assertNotEqual(self.packet()[0]['review_id'],blind_packet(self.item,self.row,2,self.context,'原始需求')[0]['review_id'])
    def test_invalid_citation_preserved_as_invalid(self):
        self.row['evidence_citations']=[{'kb_id':'MISSING'}];p,k=self.packet();self.assertFalse(p['citation_checks'][0]['in_supplied_context']);self.assertEqual(p['cited_evidence'],[])
    def test_empty_context_not_filled(self):
        p,k=blind_packet(self.item,self.row,1,None,'原始需求');self.assertTrue(p['context_was_empty']);self.assertEqual(p['cited_evidence'],[])
    def test_duplicate_citation_one_excerpt(self):
        self.row['evidence_citations']*=2;self.assertEqual(len(self.packet()[0]['cited_evidence']),1)
    def test_bad_citation_shape(self):
        self.row['evidence_citations']=['invalid'];p,k=self.packet();self.assertFalse(p['citation_checks'][0]['citation_schema_valid'])
    def test_segment_selection_invariant(self):
        self.context['selected_ids'].append('not-in-block')
        with self.assertRaises(AssertionError):evidence_segments(self.context)
    def test_unknown_is_not_direct_usable(self):self.assertEqual(judge_band({'support':'direct','applicability':'unknown'},True),'other_uncertain_error')
    def test_negative_precedence(self):self.assertEqual(judge_band({'support':'direct','applicability':'explicit_match','faithfulness':'new_inference_or_synthesis'},True),'explicit_negative')
    def test_bad_anchor_uncertain(self):self.assertEqual(judge_band({'support':'contradicted'},False),'other_uncertain_error')
    def test_direct_requires_verifiability_fidelity(self):
        d={'support':'direct','applicability':'explicit_match','verifiability':'verifiable','faithfulness':'faithful_paraphrase'};self.assertEqual(judge_band(d,True),'direct_and_applicable');d['verifiability']='uncertain';self.assertEqual(judge_band(d,True),'other_uncertain_error')

if __name__=='__main__':unittest.main()
