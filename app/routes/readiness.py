"""app/routes/readiness.py — GET /api/readiness/{user_id}/{career_id}"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.scoring_engine import ScoringEngine
from app.schemas.schemas import ReadinessResponse

router = APIRouter()
_engine = ScoringEngine()


@router.get("/readiness/{user_id}/{career_id}", response_model=ReadinessResponse)
def get_readiness(user_id: int, career_id: int, db: Session = Depends(get_db)):
    """
    Computes the user's weighted career readiness score.
    readiness = Σ(skill_level × weight) / Σ(weight)
    """
    try:
        return _engine.compute_readiness(db, user_id, career_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
