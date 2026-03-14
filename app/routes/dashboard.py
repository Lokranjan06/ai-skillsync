"""app/routes/dashboard.py — GET /api/dashboard/{user_id}"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.schemas import DashboardResponse
from app.models.orm import User

router = APIRouter()
_service = DashboardService()


@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    """
    Aggregates all study logs for a user and returns:
    - Weekly study hours (grouped by ISO calendar week)
    - Current skill progress levels
    - Focus score distribution histogram
    - Summary statistics
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    try:
        return _service.get_dashboard(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")
