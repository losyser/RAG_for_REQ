"""Offline-only route/guard regressions. No network I/O."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import json

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from openai import OpenAI
from environment_transport import EnvironmentRoutingTransport, exception_types
from run_frozen import GuardedTransport, preflight, RESERVE, WORK


class RouteTests(unittest.TestCase):
    def proxy_environment(self, no_proxy=''):
        env={k:v for k,v in os.environ.items() if k.lower() not in ('http_proxy','https_proxy','all_proxy','no_proxy')}
        env.update({'HTTPS_PROXY':'http://127.0.0.1:7890','NO_PROXY':no_proxy})
        return patch.dict(os.environ,env,clear=True)  # This test process only.

    def test_standard_proxy_selection_is_preserved_without_network(self):
        with self.proxy_environment():
            adapter=EnvironmentRoutingTransport(httpx.Timeout(10))
            try:
                selected=adapter._client._transport_for_url(httpx.URL('https://api.deepseek.com/chat/completions'))
                self.assertEqual(type(selected._pool).__name__,'HTTPProxy')
                self.assertEqual(selected._pool._retries,0)
                self.assertFalse(adapter._client.follow_redirects)
            finally:adapter.close()

    def test_no_proxy_is_honored_without_connecting(self):
        with self.proxy_environment('api.deepseek.com'):
            adapter=EnvironmentRoutingTransport(httpx.Timeout(10))
            try:
                selected=adapter._client._transport_for_url(httpx.URL('https://api.deepseek.com/chat/completions'))
                self.assertEqual(type(selected._pool).__name__,'ConnectionPool')
                self.assertEqual(selected._pool._retries,0)
            finally:adapter.close()

    def test_guard_still_counts_sdk_request_and_rejects_extra(self):
        with tempfile.TemporaryDirectory(dir=WORK) as folder:
            adapter=EnvironmentRoutingTransport(httpx.Timeout(10))
            adapter._client.close()
            calls=[]
            def handler(request):
                calls.append(request)
                return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':0,'model':'deepseek-flash',
                    'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'{}'}}],
                    'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}})
            adapter._client=httpx.Client(transport=httpx.MockTransport(handler),follow_redirects=False)
            ledger={'attempts':[],'reserved_CNY':'0'}
            guard=GuardedTransport(adapter,ledger,Path(folder)/'mock-ledger.json')
            item=preflight()['requests'][0];guard.expected=item
            with OpenAI(api_key='offline-placeholder',base_url='https://api.deepseek.com',max_retries=0,
                        http_client=httpx.Client(transport=guard,follow_redirects=False)) as client:
                self.assertEqual(client.chat.completions.create(**item['request']).model,'deepseek-flash')
                with self.assertRaises(Exception):client.chat.completions.create(**item['request'])
            self.assertEqual(len(calls),1)
            self.assertEqual(len(ledger['attempts']),1)
            self.assertEqual(ledger['reserved_CNY'],str(RESERVE))

    def test_cause_chain_has_no_messages_or_credentials(self):
        cause=PermissionError(13,'sensitive mock message')
        top=RuntimeError('also sensitive');top.__cause__=cause
        result=exception_types(top)
        self.assertEqual([x['type'] for x in result],['RuntimeError','PermissionError'])
        self.assertEqual(result[-1]['errno'],13)
        self.assertNotIn('sensitive',json.dumps(result))


if __name__=='__main__':unittest.main()
