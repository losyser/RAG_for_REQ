import unittest
from fractions import Fraction
from reconcile import metrics

class MetricTests(unittest.TestCase):
    def test_weighted_differs_from_unweighted(self):
        rows=[{'human_normalized':{'support':'direct'},'machine_raw':{'support':'direct'},'stratum_population':10,'stratum_sample_count':1},{'human_normalized':{'support':'partial'},'machine_raw':{'support':'direct'},'stratum_population':30,'stratum_sample_count':1}]
        s=metrics(rows,'support');self.assertEqual(s['sample_agreement'],.5);self.assertEqual(s['weighted_agreement'],.25)
    def test_matrix_orientation(self):
        row={'human_normalized':{'support':'contradicted'},'machine_raw':{'support':'insufficient'},'stratum_population':35,'stratum_sample_count':5}
        s=metrics([row],'support');self.assertEqual(s['confusion_matrix']['insufficient']['contradicted'],1);self.assertEqual(s['confusion_matrix']['contradicted']['insufficient'],0)
    def test_partial_not_merged_with_direct(self):
        row={'human_normalized':{'support':'partial'},'machine_raw':{'support':'direct'},'stratum_population':64,'stratum_sample_count':5}
        self.assertEqual(metrics([row],'support')['sample_agree'],0)
    def test_fraction_weight_exact(self):
        row={'human_normalized':{'support':'partial'},'machine_raw':{'support':'partial'},'stratum_population':133,'stratum_sample_count':5}
        s=metrics([row],'support');self.assertEqual(s['weighted_agreement_exact'],'1');self.assertEqual(s['weighted_denominator'],26.6)

if __name__=='__main__':unittest.main()
