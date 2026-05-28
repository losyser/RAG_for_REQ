"""Disk-backed cache for OpenAI-compatible chat completions.

Wraps `client.chat.completions.create` so that repeated experiment runs over
the same (model, messages, temperature, max_tokens) tuple do not consume
billable API tokens.  This is essential for the multi-round comparison
experiments where G4/A1/A2 share many LLM calls.

Key design:
- Cache key is a stable sha256 of the JSON-serialised request.  Both Chinese
  and English strings are preserved verbatim (ensure_ascii=False) and dict
  keys are sorted to remove ordering ambiguity.
- The cached value mimics the OpenAI ChatCompletion response shape with at
  minimum `.choices[0].message.content` and `.model`, so existing callers
  can keep using their original attribute-access code paths.
- `force=True` bypasses the cache (useful for ablation runs).
"""
from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from diskcache import Cache

# Cache directory: project_root/data/llm_cache
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CACHE_DIR = _PROJECT_ROOT / "data" / "llm_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_cache: Cache | None = None
_cache_lock = threading.Lock()


def _get_cache() -> Cache:
    """Lazy singleton — diskcache is process-safe and thread-safe."""
    global _cache
    if _cache is None:
        with _cache_lock:
            if _cache is None:
                _cache = Cache(directory=str(_CACHE_DIR))
    return _cache


# ── Response wrapper (mimics OpenAI ChatCompletion shape) ────────────────

@dataclass
class _CachedMessage:
    content: str
    role: str = "assistant"


@dataclass
class _CachedChoice:
    message: _CachedMessage
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class _CachedResponse:
    """Minimal stand-in for OpenAI's ChatCompletion object.

    Only the fields that existing callers in this codebase touch are
    populated: `.choices[0].message.content` and `.model`.
    """
    choices: list[_CachedChoice]
    model: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "_CachedResponse":
        return cls(
            choices=[_CachedChoice(message=_CachedMessage(content=payload.get("content", "")))],
            model=payload.get("model", ""),
        )


# ── Cache key derivation ─────────────────────────────────────────────────

def _make_key(
    *,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
) -> str:
    """sha256 over the canonical JSON of the request."""
    blob = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── Public API ───────────────────────────────────────────────────────────

def cached_completion(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, Any] | None = None,
    force: bool = False,
) -> _CachedResponse:
    """Drop-in wrapper for `client.chat.completions.create(...)`.

    Returns an object with `.choices[0].message.content` and `.model`.
    The `response_format` argument is forwarded to the underlying client
    but is NOT part of the cache key — response_format only constrains
    the LLM output shape; the prompt+temperature already determines the
    semantic answer for our use case.
    """
    cache = _get_cache()
    key = _make_key(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if not force:
        hit = cache.get(key)
        if hit is not None:
            return _CachedResponse.from_payload(hit)

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format

    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or ""
    raw_model = getattr(resp, "model", "") or ""
    # Coerce to plain str — guards against non-picklable mocks in tests and
    # idiosyncratic SDK objects.  Skip cache write if content isn't a plain
    # string (which can happen in test fixtures returning MagicMocks).
    if not isinstance(content, str):
        return _CachedResponse.from_payload({"content": str(content), "model": str(raw_model)})
    returned_model = raw_model if isinstance(raw_model, str) else str(raw_model)
    try:
        cache.set(key, {"content": content, "model": returned_model})
    except Exception:
        # Don't let cache write failures break the request path.
        pass
    return _CachedResponse.from_payload({"content": content, "model": returned_model})


def cache_dir() -> Path:
    """Expose the cache directory for diagnostics / probes."""
    return _CACHE_DIR


def cache_stats() -> dict[str, Any]:
    """Return basic stats for manifest writing / debugging."""
    cache = _get_cache()
    return {
        "directory": str(_CACHE_DIR),
        "size_entries": len(cache),
    }
