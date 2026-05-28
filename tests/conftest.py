"""Test fixtures.

Clears the on-disk LLM response cache before each test so that mocks
patched onto `client.chat.completions.create` are actually exercised
instead of being short-circuited by a previous run's cached payload.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_llm_cache():
    try:
        from cooling_rag_mg.llm_cache import _get_cache
    except Exception:
        yield
        return
    _get_cache().clear()
    yield
    _get_cache().clear()
