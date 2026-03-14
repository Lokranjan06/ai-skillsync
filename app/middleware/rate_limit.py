"""
app/middleware/rate_limit.py
-----------------------------
Simple in-process sliding-window rate limiter middleware.

Limits each IP to RATE_LIMIT_PER_MINUTE requests per 60-second window.
For production clusters replace with a Redis-backed implementation
(e.g. slowapi + Redis) so limits are shared across workers.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter keyed by client IP address."""

    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self._limit = requests_per_minute or get_settings().RATE_LIMIT_PER_MINUTE
        # IP → deque of request timestamps
        self._counters: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Health and docs endpoints are exempt
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._counters[ip]

        # Evict timestamps outside the sliding window
        while window and window[0] < now - _WINDOW_SECONDS:
            window.popleft()

        if len(window) >= self._limit:
            logger.warning("Rate limit exceeded for IP %s on %s", ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": f"Rate limit exceeded. Max {self._limit} requests per minute.",
                    "data": None,
                },
                headers={"Retry-After": str(_WINDOW_SECONDS)},
            )

        window.append(now)
        return await call_next(request)
