"""Offline synthetic tests. These do not constitute human ratings."""
import unittest, json, random, re, copy, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
import analyze as a

H=a.HERE; C=a.COORD; E=H/'outputs/01a13537-s3/01_仅此目录可发评审'
T=E/'数值候选独立评分.xlsx'
S=a.read(C/'SAMPLE_FROZEN.json'); B=a.read(H/'blind_input.json')
N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def fixture(name,edits=None,complete=True):
    """Mutate copies of XML only for deliberately synthetic validation fixtures."""
    changes={'xl/worksheets/sheet1.xml':{},'xl/worksheets/sheet3.xml':{}}
    if complete:
        vals=['SYNTHETIC_TEST_ONLY','外部非作者领域评审','Synthetic experience','Test only','无','是','独立首判','2026-10-20T09:00:00+08:00','2026-10-20T10:00:00+08:00']
        changes['xl/worksheets/sheet1.xml']={f'B{i}':v for i,v in enumerate(vals,6)}
        for i in range(6,56):
            for col,v in zip('BCDEF',['正确','适用','SYNTHETIC reference p1 test only','2','SYNTHETIC']):changes['xl/worksheets/sheet3.xml'][f'{col}{i}']=v
    for sheet,values in (edits or {}).items():changes.setdefault(f'xl/worksheets/sheet{sheet}.xml',{}).update(values)
    dest=H/'test_outputs'/name;dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(T) as src,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            content=src.read(info.filename)
            if info.filename in changes:
                root=ET.fromstring(content)
                for coord,v in changes[info.filename].items():
                    cell=root.find(f'.//s:c[@r="{coord}"]',N)
                    if cell is None:
                        row=root.find(f'.//s:row[@r="{re.search(r"[0-9]+",coord)[0]}"]',N)
                        cell=ET.SubElement(row,'{'+N['s']+'}c',{'r':coord})
                    for child in list(cell):cell.remove(child)
                    cell.set('t','inlineStr')
                    if v is not None:
                        if str(v).startswith('='):
                            cell.attrib.pop('t',None);ET.SubElement(cell,'{'+N['s']+'}f').text=v[1:]
                        else:ET.SubElement(ET.SubElement(cell,'{'+N['s']+'}is'),'{'+N['s']+'}t').text=v
                content=ET.tostring(root,encoding='utf-8',xml_declaration=True)
            dst.writestr(info,content)
    return dest

def row(s,arm,c='正确',app='适用',id='x'):
    return dict(source_id=s,arm=arm,correctness=c,applicability=app,blind_id=id,basis='test')

class ReviewTests(unittest.TestCase):
    def test_sample_counts_and_identity(self):
        self.assertEqual(Counter(r['arm'] for r in S),{'rag':25,'norag':25})
        self.assertEqual(len({r['source_id'] for r in S}),20)
        self.assertEqual(len({r['stable_id'] for r in S}),50)
        self.assertEqual(len({r['blind_id'] for r in S}),50)
        grouped=Counter((r['source_id'],r['arm']) for r in S)
        self.assertEqual(sum(n==2 for n in grouped.values()),10)
        for s,arm in grouped:self.assertEqual(grouped[s,arm],grouped[s,'norag' if arm=='rag' else 'rag'])
    def test_reproduce_draw(self):
        p=a.read(C/'CANDIDATE_POOL_FROZEN.json');m=a.read(C/'SAMPLING.json');seed=m['seed']
        extra=sorted(random.Random(str(seed)+'|extra_sources').sample(m['supplement_eligible'],5))
        self.assertEqual(extra,m['supplement_selected']);out=[]
        for s in m['common_sources']:
            for arm in ['rag','norag']:
                frame=sorted([r for r in p[arm] if r['source_id']==s],key=lambda r:r['row_1based'])
                out.extend(random.Random(f'{seed}|within|{s}|{arm}').sample(frame,2 if s in extra else 1))
        random.Random(str(seed)+'|display_order').shuffle(out)
        self.assertEqual([r['stable_id'] for r in out],[r['stable_id'] for r in S])
        self.assertEqual([f'K{n}' for n in random.Random(str(seed)+'|blind_ids').sample(range(100000,1000000),50)],[r['blind_id'] for r in S])
    def test_display_text_exact_and_no_tbd(self):
        for b,s in zip(B,S):
            self.assertEqual(b['original_requirement'],s['original_requirement'])
            for k in ['shall_statement','measurable_criterion','applicable_condition','verification_method','acceptance_criteria']:self.assertEqual(b[k],s['candidate'].get(k))
            self.assertNotRegex(b['measurable_criterion'],r'(?i)\bTBD\b')
            self.assertEqual(set(b),{'blind_id','original_requirement','shall_statement','measurable_criterion','applicable_condition','verification_method','acceptance_criteria'})
    def test_inputs_and_historical_protection(self):
        for path,h in a.read(C/'PROTECTED_BEFORE.json').items():self.assertEqual(a.sha(path),h,path)
        for n,h in a.read(C/'CHECKPOINT.json')['dirty_backup_hashes'].items():self.assertEqual(a.sha(H.parents[1]/n),h,n)
        for v in a.read(C/'INPUT_MANIFEST.json').values():self.assertEqual(a.sha(H/v['snapshot']),v['sha256'])
    def test_blank_and_full_text(self):
        wb=a.openpyxl.load_workbook(T,data_only=False)
        self.assertEqual(len(wb.sheetnames),4)
        self.assertTrue(all(wb['身份与说明'][f'B{i}'].value is None for i in range(6,15)))
        self.assertTrue(all(wb['评分50'].cell(i,j).value is None for i in range(6,56) for j in range(2,7)))
        self.assertEqual(len(wb['评分50'].data_validations.dataValidation),3)
        chunks=defaultdict(str)
        for code,label,text in wb['完整原文'].iter_rows(min_row=6,values_only=True):
            if code:chunks[code,re.sub(r'（\d+/\d+）$','',label)]+=text or ''
        labels=['原需求','候选要求','数值判据','适用条件','验证方法','验收内容']
        keys=['original_requirement','shall_statement','measurable_criterion','applicable_condition','verification_method','acceptance_criteria']
        for b in B:
            for label,k in zip(labels,keys):self.assertEqual(chunks[b['blind_id'],label],'\n'.join(b[k]) if isinstance(b[k],list) else str(b[k] or ''))
        wb.close()
    def test_html_readonly(self):
        import html
        content=(E/'50条原文只读阅读.html').read_text(encoding='utf8')
        self.assertEqual(content.count('<article '),50)
        self.assertNotRegex(content,r'(?i)<(input|script|textarea|form)\b|https?://|evidence_citations|source_requirement_id')
        for b in B:
            for k,v in b.items():self.assertIn(html.escape('\n'.join(v) if isinstance(v,list) else str(v or '')),content)
    def test_blank_blocks(self):
        v=a.validate(T,a.contract(T),S);self.assertFalse(v['valid']);self.assertIsNone(v['ratings'])
    def test_complete_synthetic_valid(self):self.assertTrue(a.validate(fixture('SYNTHETIC_valid.xlsx'),a.contract(T),S)['valid'])
    def test_invalid_cases(self):
        cases=[{1:{'B6':None}},{1:{'B7':'invented'}},{1:{'B11':'否'}},{1:{'B12':'讨论后修订'}},{1:{'B13':'2026-10-20'}},{3:{'D6':None}},{3:{'B6':None}},{3:{'E6':'4'}},{3:{'D6':'=1+1'}},{3:{'A6':S[1]['blind_id']}},{4:{'C6':'altered'}}]
        for i,edits in enumerate(cases):
            with self.subTest(i=i):self.assertFalse(a.validate(fixture(f'SYNTHETIC_invalid_{i}.xlsx',edits),a.contract(T),S)['valid'])
    def test_unknown_truth_table(self):
        self.assertEqual(a.status(row('s','rag','错误','工况不明')),(0,0))
        self.assertEqual(a.status(row('s','rag','无法判断','不适用')),(0,0))
        self.assertEqual(a.status(row('s','rag','正确','工况不明')),(0,1))
        self.assertEqual(a.status(row('s','rag','可接受')),(0,0))
        self.assertEqual(a.status(row('s','rag','可接受'),True),(1,0))
    def test_source_equal_not_item_equal(self):
        rows=[row('s1','rag'),row('s1','norag','错误')]+[row('s2',arm,'错误' if arm=='rag' else '正确') for arm in ['rag','norag'] for _ in range(2)]
        out=a.outcome(rows);self.assertEqual(out['source_equal_difference'],0);self.assertAlmostEqual(out['item_descriptive']['rag']['confirmed_success_fraction'],1/3)
    def test_reverse_unknown_bounds(self):
        out=a.outcome([row('s','rag','无法判断'),row('s','norag','无法判断')]);self.assertEqual(out['unknown_assignment_bounds'],[-1,1])
        out=a.outcome([row('s','rag'),row('s','norag','无法判断')]);self.assertEqual(out['unknown_assignment_bounds'],[0,1])
    def test_sign_ties_and_exact(self):
        self.assertIsNone(a.sign_test([0]*20)['two_sided_p']);self.assertEqual(a.sign_test([1]*5+[0])['two_sided_p'],.0625)
    def test_nominal_agreement_unknown(self):
        first=[row('s','rag','正确',id='1'),row('s','rag','无法判断',id='2')];second=copy.deepcopy(first)
        self.assertEqual(a.agreement(first,second)['correctness']['kappa'],1)
        second[1]['correctness']='正确';self.assertEqual(a.agreement(first,second)['correctness']['kappa'],0)
        self.assertIsNone(a.agreement(first,second)['applicability']['kappa'])

if __name__=='__main__':unittest.main(verbosity=2)
