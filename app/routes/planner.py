"""app/routes/planner.py — POST /api/generate-plan"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.planner_engine import PlannerEngine
from app.schemas.schemas import PlannerRequest, PlannerResponse

router = APIRouter()
_engine = PlannerEngine()


@router.post("/generate-plan", response_model=PlannerResponse)
def generate_plan(request: PlannerRequest, db: Session = Depends(get_db)):
    """
    Generates a prioritised study plan.
    priority = (1 - skill_level) × weight × (1 / exam_days_left)
    Returns the top-N highest priority skills to work on.
    """
    try:
        return _engine.generate_plan(db, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planner error: {str(e)}")
