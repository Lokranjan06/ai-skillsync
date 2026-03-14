"""
app/core/cache.py
------------------
Lightweight in-process TTL cache.

Used by the skill-graph engine and job-matching engine to avoid
recomputing expensive queries on every request.

For multi-process / distributed deployment replace this with
a Redis-backed cache (e.g. aiocache + Redis) without changing callers.
"""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """Thread-safe-enough in-memory key-value store with per-entry TTL."""

    def __init__(self, default_ttl: int = 300) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None


# Global cache instances
skill_graph_cache = TTLCache(default_ttl=300)
job_match_cache   = TTLCache(default_ttl=120)
