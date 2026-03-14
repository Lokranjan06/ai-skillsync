"""app/routes/simulation.py — POST /api/simulate-score"""

from fastapi import APIRouter, HTTPException, Request

from app.schemas.schemas import SimulationRequest, SimulationResponse

router = APIRouter()


@router.post("/simulate-score", response_model=SimulationResponse)
def simulate_score(request: SimulationRequest, raw_request: Request):
    """
    Digital Twin: predicts an exam score using a pre-trained
    LinearRegression model (study_hours, focus_score, revision_frequency).
    The model is trained at startup and stored in app.state.
    """
    engine = getattr(raw_request.app.state, "prediction_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Prediction engine not initialised.")
    try:
        return engine.predict(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
