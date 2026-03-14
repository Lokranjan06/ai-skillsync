"""app/routes/burnout.py — POST /api/burnout-risk"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.burnout_service import BurnoutService
from app.schemas.schemas import BurnoutRequest, BurnoutResponse

router = APIRouter()
_service = BurnoutService()


@router.post("/burnout-risk", response_model=BurnoutResponse)
def assess_burnout(request: BurnoutRequest, db: Session = Depends(get_db)):
    """
    Evaluates burnout risk using:
        risk = (7 - sleep)×0.4 + (study/10)×0.3 + ((100-focus)/100)×0.3
    Returns Low / Medium / High classification with actionable advice.
    """
    # db injected for future persistence (log burnout checks over time)
    return _service.assess(request)
