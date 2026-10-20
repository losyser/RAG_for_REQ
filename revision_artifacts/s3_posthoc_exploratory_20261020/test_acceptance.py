import unittest
from explore import *

class ExplorationAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input=H/'input_archive/v3_normalized.xlsx';cls.temp=H/'private_tests';cls.temp.mkdir(exist_ok=True)

    def mutate(self,name,sheet,cell,value):
        p=self.temp/(name+'.xlsx');w=tc.ORIGINAL_LOADER(self.input);w[sheet][cell]=value;w.save(p);w.close();return p

    def test_admin_missing_is_warning_never_completed(self):
        x=accept_for_exploration(self.input)
        self.assertTrue(x['score_data_complete']);self.assertFalse(x['original_frozen_process_valid']);self.assertFalse(x['claims_frozen_process_acceptance']);self.assertFalse(x['process_record_complete']);self.assertEqual(len(x['warnings']),9)
        self.assertEqual(len(x['ratings']),50)

    def test_original_text_tamper_rejected(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('text','完整原文','C6','TAMPER'))

    def test_missing_score_rejected(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('score','评分50','B6',None))

    def test_missing_applicability_rejected(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('applicability','评分50','C6',None))

    def test_missing_positive_basis_rejected(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('basis','评分50','D8',None))

    def test_formula_rejected(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('formula','评分50','E6','=1+1'))

    def test_unknown_id_rejected(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('id','评分50','A6','OTHER'))

    def test_explicit_nonindependence_not_silently_overridden(self):
        with self.assertRaises(ValueError):accept_for_exploration(self.mutate('process','身份与说明','B11','否'))

if __name__=='__main__':unittest.main(verbosity=2)
