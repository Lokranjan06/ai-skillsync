"""
app/routes/resume_optimizer.py
--------------------------------
POST /api/resume-optimize

Accepts a PDF résumé and returns:
  • ATS compatibility score (0-100)
  • Score breakdown by dimension
  • Missing high-value keywords
  • Prioritised improvement suggestions
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.responses import APIResponse
from app.database.session import get_db
from app.services.resume_optimizer import ResumeOptimizerService

logger = get_logger(__name__)
router = APIRouter()

_service = ResumeOptimizerService()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post(
    "/resume-optimize",
    summary="ATS Resume Optimizer",
    description=(
        "Analyses a PDF résumé for ATS compatibility. "
        "Returns a score breakdown and actionable improvement suggestions."
    ),
    tags=["Resume Optimizer"],
)
async def optimize_resume(
    file: UploadFile = File(..., description="PDF résumé to analyse"),
    db: Session = Depends(get_db),
) -> APIResponse:
    # Content-type guard
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are accepted. Received: {file.content_type or 'unknown'}",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit.")

    try:
        result = _service.analyze(file_bytes)
        logger.info(
            "ATS analysis complete for '%s' — score: %.1f",
            file.filename, result["ats_score"],
        )
        return APIResponse.ok(result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume optimization failed for file '%s'", file.filename)
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc
