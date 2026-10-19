"""Synthetic end-to-end aggregation; never dispatches model calls."""
import contextlib,copy,csv,io,json,tempfile,unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import terminal_report330 as report
import transport as t

class TerminalIntegrationTests(unittest.TestCase):
    def test_440_successes_two_failures_keep_quarantine_and_block_formal_sample(self):
        with tempfile.TemporaryDirectory() as td:
            work=Path(td);here=work/'continuation';here.mkdir();old=work/'review';old.mkdir();new=here/'review';new.mkdir();prev=work/'previous';prev.mkdir();middle=prev/'review';middle.mkdir()
            plan=[];keys=[];packets=[]
            for i in range(441):
                rid=f'test-{i:03d}';group='semantic_new' if i%2==0 else 'random_new';body={'test':i}
                plan.append({'review_id':rid,'slot':rid,'body_sha256':t.digest(body)})
                keys.append({'review_id':rid,'slot':rid,'source_id':f'OR{i%60+1:03d}','group':group,'row_index':1})
                packets.append({'review_id':rid,'source_requirement':'synthetic','candidate':{},'cited_evidence':[{'evidence_id':'E001','supplied_excerpt':'synthetic evidence'}]})
            def save(path,value):path.write_text(json.dumps(value),encoding='utf8')
            for folder,indices in [(old,range(78)),(middle,range(77,111)),(new,range(111,441))]:
                for n,i in enumerate(indices,1):
                    x=plan[i];a={'slot':x['slot'],'body_sha256':x['body_sha256'],'endpoint':t.PROVIDERS['review']['endpoint'],'reserved_CNY':'0.0933888','started_at':'2026-10-19T00:00:00Z'}
                    r={'status':'failed_stop','slot':x['slot']} if (folder==old and i==77) or (folder==middle and i==110) else {'status':'completed','slot':x['slot'],'parsed':{'review_id':x['review_id'],'support':['direct','partial','contradicted','insufficient','uncertain'][i%5],'applicability':'unknown','anchors':[{'evidence_id':'E001','exact_quote':'synthetic evidence'}]},'identity':{'model':'qwen-max','system_fingerprint':None},'response':{'id':f'unique-{i}','model':'qwen-max','usage':{'prompt_tokens':100,'completion_tokens':200,'total_tokens':300,'prompt_tokens_details':{'cached_tokens':0}}},'usage_cost_CNY':'0.00216'}
                    save(folder/f'{n:04d}_attempt.json',a);save(folder/f'{n:04d}_response.json',r)
            for name,value in [('QWEN_FROZEN_PLAN.json',{'requests':plan}),('QWEN_BLIND_PACKETS.json',packets),('QWEN_BLIND_KEY_LOCAL_ONLY.json',keys),('FINAL_AUDIT.json',{'phases':{'generation':{'usage_estimate_CNY':'4.650044'}}}),('SOURCE_LEVEL_COUNTS.json',[{'source_id':f'OR{i+1:03d}'} for i in range(60)]),('PAIRED_SOURCE_DIFFERENCES.json',[]),('RUN_PREFLIGHT.json',{'protected_hashes':{},'frozen_hashes':{}})]:save(work/name,value)
            save(new/'state.json',{'status':'completed','debit_CNY':str(Decimal('0.563162')+Decimal('4.650044')+440*Decimal('0.00216')+Decimal('4.325376')+2*Decimal('0.0933888'))})
            save(prev/'sampling_policy_v5.json',t.read(report.resume.PREVIOUS/'sampling_policy_v5.json'));save(here/'PREVIOUS_ARTIFACT_HASHES.json',{})
            old_hash=t.sha(old/'0078_response.json')
            with patch.object(report,'WORK',work),patch.object(report,'HERE',here),patch.object(report.resume,'PREVIOUS',prev),patch.object(report.resume,'preflight',return_value=None),contextlib.redirect_stdout(io.StringIO()):report.main()
            result=t.read(here/'terminal_results/FINAL_REPORT.json')
            self.assertEqual(result['unique_successful_reviews'],440);self.assertEqual(result['total_review_attempts_including_old_failure'],442)
            self.assertEqual(result['formal_sample_count'],0);self.assertEqual(result['Qwen_successful_tokens']['total_tokens'],440*300)
            self.assertEqual(t.sha(old/'0078_response.json'),old_hash)
            self.assertFalse((here/'terminal_results/manual_sample').exists())
            self.assertEqual(result['sample_block'],'all441_not_completed')
            self.assertEqual(len(t.read(here/'terminal_results/PAIRED_SOURCE_REVIEW_DIFFERENCES.json')),60)

if __name__=='__main__':unittest.main()
