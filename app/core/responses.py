"""
app/core/responses.py
----------------------
Standardised API envelope used across all new endpoints.

Every response from the new features follows this shape:
    {
        "success": true,
        "data": { ... },
        "error": null,
        "meta": { "version": "2.0.0", "timestamp": "..." }
    }

Existing endpoints keep their original response_model untouched.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.core.config import get_settings

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: str | None = None
    meta: dict[str, Any] = {}

    @classmethod
    def ok(cls, data: T) -> "APIResponse[T]":
        return cls(
            success=True,
            data=data,
            error=None,
            meta={
                "version": get_settings().APP_VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @classmethod
    def fail(cls, message: str, code: int = 400) -> "APIResponse[None]":
        return cls(
            success=False,
            data=None,
            error=message,
            meta={
                "version": get_settings().APP_VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_code": code,
            },
        )
