"""app/routes/skill_gap.py — GET /api/skill-gap/{user_id}/{career_id}"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.scoring_engine import ScoringEngine
from app.schemas.schemas import SkillGapResponse

router = APIRouter()
_engine = ScoringEngine()


@router.get("/skill-gap/{user_id}/{career_id}", response_model=SkillGapResponse)
def get_skill_gap(user_id: int, career_id: int, db: Session = Depends(get_db)):
    """
    Classifies all career-required skills into strong / weak / missing
    buckets based on the user's current progress.
    """
    try:
        return _engine.compute_skill_gap(db, user_id, career_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
