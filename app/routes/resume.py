"""app/routes/resume.py — POST /api/extract-resume"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.resume_extractor import ResumeExtractor
from app.schemas.schemas import ResumeExtractResponse

router = APIRouter()
_extractor = ResumeExtractor()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/extract-resume", response_model=ResumeExtractResponse)
async def extract_resume(
    file: UploadFile = File(..., description="PDF résumé to analyse"),
    db:   Session    = Depends(get_db),
):
    """
    Accepts a PDF résumé upload, extracts plain text, and matches the
    content against all skills stored in the database using keyword matching.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Received: " + (file.content_type or "unknown"),
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit.")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return _extractor.extract(db, file_bytes, filename=file.filename or "resume.pdf")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parsing failed: {e}")
