"""
app/core/exceptions.py
-----------------------
Domain exceptions and FastAPI exception handlers.

Raises typed exceptions in services → handlers convert them to
consistent JSON error responses — no more ad-hoc HTTPException scattered
throughout business logic.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------

class SkillSyncError(Exception):
    """Base exception for all AI SkillSync domain errors."""
    status_code: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundError(SkillSyncError):
    status_code = 404
    message = "Resource not found."


class ValidationError(SkillSyncError):
    status_code = 422
    message = "Input validation failed."


class ServiceUnavailableError(SkillSyncError):
    status_code = 503
    message = "A required service is not available."


class FileTooLargeError(SkillSyncError):
    status_code = 413
    message = "Uploaded file exceeds the size limit."


# ---------------------------------------------------------------------------
# FastAPI Exception Handlers
# ---------------------------------------------------------------------------

def _error_body(status_code: int, message: str) -> dict:
    from datetime import datetime, timezone
    return {
        "success": False,
        "data": None,
        "error": message,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_code": status_code,
        },
    }


async def skillsync_exception_handler(
    request: Request, exc: SkillSyncError
) -> JSONResponse:
    logger.warning("Domain error on %s %s: %s", request.method, request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.status_code, exc.message),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_body(500, "Internal server error. Please try again later."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SkillSyncError, skillsync_exception_handler)   # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)         # type: ignore[arg-type]
