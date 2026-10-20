import unittest
from classifier_v2 import classify

class QFormatTests(unittest.TestCase):
    def row(self,**kw):
        return dict({'measurable_criterion':'[Q] 报警器应发出声光信号','applicable_condition':'报警触发时','evidence_citations':[{'kb_id':'E1'}]},**kw)
    def check(self,row,selected=('E1',)):
        return classify(row,{'E1','E2'},set(selected))
    def test_format_is_not_semantics(self):
        r=self.check(self.row()); self.assertEqual(r['q_format'],'pass'); self.assertEqual(r['semantic_support'],'not_assessed');self.assertEqual(r['legacy_grade_action'],'unchanged_not_promoted')
    def test_valid_id_outside_context(self): self.assertIn('citation_not_in_context',self.check(self.row(evidence_citations=[{'kb_id':'E2'}]))['format_errors'])
    def test_unknown_id(self): self.assertIn('citation_not_in_kb',self.check(self.row(evidence_citations=[{'kb_id':'E9'}]))['format_errors'])
    def test_no_cites(self): self.assertEqual(self.check(self.row(evidence_citations=[]))['q_format'],'fail')
    def test_bad_cite_shape(self): self.assertEqual(self.check(self.row(evidence_citations=['E1']))['q_format'],'fail')
    def test_wrong_cites_type(self): self.assertEqual(self.check(self.row(evidence_citations='E1'))['q_format'],'fail')
    def test_one_invalid_among_valid(self): self.assertEqual(self.check(self.row(evidence_citations=[{'kb_id':'E1'},{'kb_id':'E9'}]))['q_format'],'fail')
    def test_empty_q(self): self.assertIn('empty_q_body',self.check(self.row(measurable_criterion='[Q] '))['format_errors'])
    def test_q_position(self): self.assertIn('prefix_not_at_start',self.check(self.row(measurable_criterion='备注[Q]报警'))['format_errors'])
    def test_missing_condition(self): self.assertEqual(self.check(self.row(applicable_condition=''))['q_format'],'fail')
    def test_unknown_condition_not_direct(self):
        r=self.check(self.row(applicable_condition='机型工况未知'));self.assertEqual(r['q_format'],'pass');self.assertEqual(r['applicability'],'unknown')
    def test_semantically_bad_passes_only_format(self):
        r=self.check(self.row(measurable_criterion='[Q] 系统应非常优秀'));self.assertEqual(r['q_format'],'pass');self.assertEqual(r['semantic_support'],'not_assessed')
    def test_mixed_q_tbd(self): self.assertIn('mixed_q_tbd',self.check(self.row(measurable_criterion='[Q] {{TBD|unit:bar}}'))['format_errors'])
    def test_empty_context(self): self.assertIn('empty_context_requires_tbd',self.check(self.row(),())['format_errors'])
    def test_single_brace(self): self.assertEqual(self.check(self.row(measurable_criterion='{TBD|unit:bar}'))['class'],'tbd_or_mixed_candidate')
    def test_double_brace(self): self.assertEqual(self.check(self.row(measurable_criterion='{{TBD|unit:bar}}'))['class'],'tbd_or_mixed_candidate')
    def test_numeric(self): self.assertEqual(self.check(self.row(measurable_criterion='≤12 dGH'))['class'],'numeric_candidate')
    def test_unmarked(self): self.assertEqual(self.check(self.row(measurable_criterion='应发出警报'))['class'],'unmarked_nonnumeric_candidate')
    def test_none_row(self): self.assertEqual(self.check(None)['class'],'invalid_row')
    def test_invalid_criterion_type(self): self.assertEqual(self.check(self.row(measurable_criterion=[]))['class'],'missing_criterion')
    def test_q_numeric_does_not_prove_support(self): self.assertEqual(self.check(self.row(measurable_criterion='[Q] 温度≤80°C'))['semantic_support'],'not_assessed')

if __name__=='__main__': unittest.main()
