"""
app/routes/career_copilot.py
------------------------------
POST /api/career-copilot

AI career mentor endpoint.
Accepts a free-text career question and returns structured,
step-by-step guidance from the career knowledge base.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.responses import APIResponse
from app.services.career_copilot import CareerCopilotService

logger = get_logger(__name__)
router = APIRouter()

_service = CareerCopilotService()


# ---------------------------------------------------------------------------
# Request schema (defined here to keep schemas.py for existing features only)
# ---------------------------------------------------------------------------

class CopilotRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Career question to ask the AI mentor",
        examples=["How do I become an AI engineer?"],
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/career-copilot",
    summary="AI Career Copilot",
    description=(
        "Ask the AI career mentor any career question. "
        "Returns structured step-by-step guidance, pro tips, and learning resources."
    ),
    tags=["Career Copilot"],
)
def career_copilot(request: CopilotRequest) -> APIResponse:
    try:
        result = _service.answer(request.question)
        logger.info(
            "Career copilot answered question (topic: %s, confidence: %s)",
            result.get("topic"), result.get("confidence"),
        )
        return APIResponse.ok(result)
    except Exception as exc:
        logger.exception("Career copilot failed for question: %s", request.question[:80])
        raise HTTPException(status_code=500, detail=f"Copilot error: {exc}") from exc
