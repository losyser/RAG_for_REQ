"""Synthetic declarations are test fixtures only, never reviewer data or analysis inputs."""
import unittest
from technical_cleanup import *

class CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=H/'private_tests';cls.temp.mkdir(exist_ok=True)
        cls.good=cls.temp/'SYNTHETIC_TEST_ONLY.xlsx'
        wb=ORIGINAL_LOADER(OUT);ws=wb['身份与说明']
        fields={6:'SYNTHETIC_TEST_NOT_A_REVIEWER',7:'其他（备注说明）',8:'SYNTHETIC validation fixture only',10:'SYNTHETIC',11:'是',12:'独立首判',13:'2026-01-01T00:00:00+00:00',14:'2026-01-01T00:01:00+00:00'}
        for row,value in fields.items():ws.cell(row,2).value=value
        wb.save(cls.good);wb.close()

    def variant(self,name,sheet,cell,value):
        p=self.temp/(name+'.xlsx');wb=ORIGINAL_LOADER(self.good);wb[sheet][cell]=value;wb.save(p);wb.close();return compatible_validate(p)

    def test_only_dimension_false_positives_removed(self):
        original=frozen.validate(self.good,read(C/'WORKBOOK_CONTRACT.json'),read(C/'SAMPLE_FROZEN.json'))
        self.assertTrue(original['issues']);self.assertTrue(all('行列范围改变' in x for x in original['issues']))
        self.assertTrue(compatible_validate(self.good)['valid'])

    def test_tampered_candidate_rejected(self):
        r=self.variant('tampered','完整原文','C6','SYNTHETIC TAMPER');self.assertFalse(r['valid']);self.assertTrue(any('原文/盲ID/定义/结构' in x for x in r['issues']))

    def test_missing_rating_rejected(self):
        r=self.variant('missing_rating','评分50','C10',None);self.assertFalse(r['valid']);self.assertTrue(any('适用性未填' in x for x in r['issues']))

    def test_missing_positive_basis_rejected(self):
        r=self.variant('missing_basis','评分50','D8',None);self.assertFalse(r['valid']);self.assertTrue(any('必须填写具体依据' in x for x in r['issues']))

    def test_missing_process_rejected(self):
        r=self.variant('missing_process','身份与说明','B13',None);self.assertFalse(r['valid']);self.assertTrue(any('start_time' in x for x in r['issues']))

    def test_formula_rejected(self):
        r=self.variant('formula','评分50','E10','=1+1');self.assertFalse(r['valid']);self.assertTrue(any('禁止公式' in x for x in r['issues']))

    def test_added_content_rejected(self):
        r=self.variant('extra_content','完整原文','D356','extra');self.assertFalse(r['valid']);self.assertTrue(any('结构被修改' in x for x in r['issues']))

    def test_actual_return_still_blocked(self):
        r=compatible_validate(OUT);self.assertFalse(r['valid']);self.assertTrue(any('身份/过程字段未填' in x for x in r['issues']));self.assertFalse(any('原文/盲ID/定义/结构' in x or '行列范围改变' in x for x in r['issues']))

if __name__=='__main__':unittest.main(verbosity=2)
