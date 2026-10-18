"""Preserve HTTPX's existing environment routing inside the request-count guard.

No proxy/VPN/system settings are changed. Importing/constructing does not send.
"""
from __future__ import annotations
import httpx


class EnvironmentRoutingTransport(httpx.BaseTransport):
    def __init__(self, timeout: httpx.Timeout):
        # Leaving transport/proxy unspecified is intentional: HTTPX then applies
        # its normal HTTPS_PROXY/ALL_PROXY/NO_PROXY routing. Its default transport
        # retry count is zero. No custom proxy endpoint is invented here.
        self._client = httpx.Client(timeout=timeout, trust_env=True, follow_redirects=False)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if request.method != 'POST' or str(request.url) != 'https://api.deepseek.com/chat/completions':
            raise RuntimeError('Environment transport only permits the approved completion endpoint')
        return self._client.send(request, stream=True)

    def close(self):
        self._client.close()


def exception_types(exc: BaseException) -> list[dict]:
    """Cause information without messages, URLs, headers, credentials or env values."""
    out, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        out.append({'type': type(exc).__name__, 'errno': getattr(exc, 'errno', None),
                    'winerror': getattr(exc, 'winerror', None)})
        exc = exc.__cause__ or exc.__context__
    return out
