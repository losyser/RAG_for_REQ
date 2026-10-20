"""Offline integration: prior failure + 11 mock HTTP replies = cap 12."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import httpx
import run_frozen as run


class ContinuationTest(unittest.TestCase):
    def test_cumulative_attempts_and_original_failure_are_preserved(self):
        plan=run.preflight()
        prior=(run.WORK/'ledger.json').read_bytes()
        calls=[]
        def handler(request):
            calls.append(request)
            return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':0,'model':'deepseek-flash',
                'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'{}'}}],
                'usage':{'prompt_tokens':100,'completion_tokens':10,'total_tokens':110}})
        with tempfile.TemporaryDirectory(dir=run.WORK) as folder:
            work=Path(folder);(work/'ledger.json').write_bytes(prior)
            with patch.object(run,'WORK',work), patch.object(run,'preflight',return_value=plan), \
                 patch.object(run,'hashes_unchanged',return_value={'protected_count':366}), \
                 patch.object(run,'EnvironmentRoutingTransport',side_effect=lambda timeout:httpx.MockTransport(handler)), \
                 patch('cooling_rag_mg.config.DeepSeekConfig',return_value=SimpleNamespace(base_url='https://api.deepseek.com',api_key='offline-placeholder')), \
                 contextlib.redirect_stdout(io.StringIO()):
                run.main(True,True)
                with self.assertRaises(FileExistsError):run.main(True,True)
            ledger=json.loads((work/'continuation_ledger.json').read_text('utf-8'))
            self.assertEqual(len(calls),11)
            self.assertEqual(len(ledger['attempts']),12)
            self.assertEqual(ledger['attempts'][0]['status'],'failed_stop')
            self.assertEqual(ledger['attempts'][1]['case'],'OR001')
            self.assertEqual(ledger['attempts'][1]['arm'],'new')
            self.assertEqual(ledger['reserved_CNY'],'25.952256')
            self.assertEqual(ledger['status'],'completed_remaining_11_with_prior_failure')
            self.assertEqual((work/'ledger.json').read_bytes(),prior)


if __name__=='__main__':unittest.main()
