"""Standalone offline transport/ledger tests; no production cache or network."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import httpx
from openai import OpenAI
import run_frozen as run


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=run.WORK)
        self.path=Path(self.temp.name)/'ledger.json'
        self.item=copy.deepcopy(run.preflight()['requests'][0])
        self.ledger={'attempts':[],'reserved_CNY':'0'}
        self.seen=[]
        def handler(request):
            self.seen.append(request)
            return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':0,'model':'deepseek-flash',
                'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'{"shalls":[]}'}}],
                'usage':{'prompt_tokens':100,'completion_tokens':10,'total_tokens':110}})
        self.guard=run.GuardedTransport(httpx.MockTransport(handler),self.ledger,self.path)
        self.client=OpenAI(api_key='offline-placeholder',base_url='https://api.deepseek.com',max_retries=0,
            http_client=httpx.Client(transport=self.guard,follow_redirects=False))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def send(self):
        self.guard.expected=self.item
        return self.client.chat.completions.with_raw_response.create(**self.item['request'])

    def test_real_sdk_serialization_matches_frozen_and_logs_once(self):
        raw=self.send()
        self.assertEqual(raw.parse().usage.prompt_tokens,100)
        self.assertIsInstance(raw.text,str)
        self.assertEqual(len(self.seen),1)
        self.assertEqual(self.ledger['reserved_CNY'],str(run.RESERVE))
        self.assertEqual(len(json.loads(self.path.read_text())['attempts']),1)

    def test_thirteenth_request_blocked_before_dispatch(self):
        self.ledger['attempts']=[{'reserved_CNY':str(run.RESERVE)} for _ in range(12)]
        with self.assertRaises(Exception):self.send()
        self.assertEqual(len(self.seen),0)

    def test_body_mutation_blocked(self):
        self.guard.expected=self.item
        req=copy.deepcopy(self.item['request']);req['max_tokens']=8193
        with self.assertRaises(Exception):self.client.chat.completions.create(**req)
        self.assertEqual(len(self.seen),0)

    def test_timeout_keeps_reservation_no_retry(self):
        def fail(request):
            self.seen.append(request)
            raise httpx.ReadTimeout('mock timeout',request=request)
        self.guard.delegate=httpx.MockTransport(fail)
        with self.assertRaises(Exception):self.send()
        self.assertEqual(len(self.seen),1)
        self.assertEqual(len(self.ledger['attempts']),1)
        self.assertEqual(self.ledger['reserved_CNY'],str(run.RESERVE))

    def test_budget_cap_blocks_before_dispatch(self):
        self.ledger['attempts']=[{'reserved_CNY':'39'}]
        with self.assertRaises(Exception):self.send()
        self.assertEqual(len(self.seen),0)


if __name__=='__main__':unittest.main()
