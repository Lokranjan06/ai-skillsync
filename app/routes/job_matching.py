"""
app/routes/job_matching.py
---------------------------
GET /api/job-matches/{user_id}

Returns AI-powered job role recommendations based on the user's
skill profile stored in the database.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.responses import APIResponse
from app.database.session import get_db
from app.models.orm import User
from app.services.job_matching_service import JobMatchingService

logger = get_logger(__name__)
router = APIRouter()

_service = JobMatchingService()


@router.get(
    "/job-matches/{user_id}",
    summary="AI Job Matching",
    description=(
        "Compares the user's skill profile against a registry of tech job roles. "
        "Returns match percentages, matched skills, and top skill gaps per role."
    ),
    tags=["Job Matching"],
)
def get_job_matches(
    user_id: int = Path(..., ge=1, description="User ID to match jobs for"),
    db: Session = Depends(get_db),
) -> APIResponse:
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")

    try:
        result = _service.get_job_matches(db, user_id)
        logger.info(
            "Job matches for user %d: %d recommendations",
            user_id, len(result.get("recommended_jobs", [])),
        )
        return APIResponse.ok(result)
    except Exception as exc:
        logger.exception("Job matching failed for user %d", user_id)
        raise HTTPException(status_code=500, detail=f"Job matching error: {exc}") from exc
