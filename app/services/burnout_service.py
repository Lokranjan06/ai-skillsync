"""
app/services/burnout_service.py
---------------------------------
Burnout Risk Detection — Feature #6

Risk formula (produces a score in roughly 0–4 range):
    risk = (7 - sleep) × 0.4
           + (study / 10) × 0.3
           + ((100 - focus) / 100) × 0.3

Classification thresholds:
    Low    : risk < 1.0
    Medium : 1.0 ≤ risk < 2.0
    High   : risk ≥ 2.0

The formula captures three independent stressors:
  • Sleep deficit   — less sleep → higher risk (optimal is 7 h)
  • Study overload  — more study hours relative to 10 h/day → higher risk
  • Focus drop      — lower focus → higher risk
"""

from app.schemas.schemas import BurnoutRequest, BurnoutResponse


class BurnoutService:
    """Stateless burnout risk detector."""

    LOW_THRESHOLD    = 1.0
    MEDIUM_THRESHOLD = 2.0

    # Advice templates keyed by risk level
    _ADVICE: dict[str, str] = {
        "Low": (
            "Your current study habits look healthy. "
            "Keep maintaining regular sleep and planned breaks."
        ),
        "Medium": (
            "Signs of stress are emerging. Consider reducing daily study hours, "
            "improving sleep consistency, and adding short mindfulness breaks."
        ),
        "High": (
            "High burnout risk detected. Immediately reduce study intensity, "
            "prioritise 7–9 hours of sleep, and take at least one full rest day. "
            "Consider speaking with a mentor or counsellor."
        ),
    }

    def assess(self, request: BurnoutRequest) -> BurnoutResponse:
        risk_score = self._calculate_risk(
            sleep=request.sleep_hours,
            study=request.study_hours,
            focus=request.focus_score,
        )
        risk_level = self._classify(risk_score)

        return BurnoutResponse(
            user_id=request.user_id,
            risk_score=round(risk_score, 4),
            risk_level=risk_level,
            advice=self._ADVICE[risk_level],
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _calculate_risk(sleep: float, study: float, focus: float) -> float:
        sleep_component = (7 - sleep) * 0.4
        study_component = (study / 10) * 0.3
        focus_component = ((100 - focus) / 100) * 0.3
        return sleep_component + study_component + focus_component

    def _classify(self, score: float) -> str:
        if score < self.LOW_THRESHOLD:
            return "Low"
        if score < self.MEDIUM_THRESHOLD:
            return "Medium"
        return "High"
