"""
app/ai/prediction_engine.py
------------------------------
Digital Twin Simulation — Feature #7

Uses scikit-learn LinearRegression to predict exam score from:
    - study_hours        (daily average)
    - focus_score        (0–100)
    - revision_frequency (sessions per week)

The model is trained on a synthetic dataset at startup (see main.py lifespan).
In a production system this would be replaced with real historical data from
the study_logs table and retrained periodically.

Why Linear Regression?
  - Transparent and explainable (important for a learning tool)
  - Fast to train and predict
  - Adequate for the feature space; swap for GradientBoosting as data grows
"""

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from app.schemas.schemas import SimulationRequest, SimulationResponse


class PredictionEngine:
    """
    Wraps a scikit-learn pipeline (scaler + GradientBoosting model).
    Thread-safe for reads once trained.
    """

    def __init__(self):
        # Pipeline: StandardScaler → GradientBoostingRegressor
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42
            )),
        ])
        self._trained = False

    # -----------------------------------------------------------------------
    # Training
    # -----------------------------------------------------------------------

    def train(self) -> None:
        """
        Pre-trains the model on a synthetic dataset.

        Synthetic ground truth:
            score = 20 + 8×study + 0.4×focus + 3×revision + noise

        This encodes the intuition that:
          • Every extra study hour contributes ~8 points
          • Focus has a smaller but meaningful effect
          • Revision frequency solidifies retention
        """
        rng = np.random.default_rng(seed=42)
        n   = 500

        study     = rng.uniform(0, 10, n)         # 0–10 hours/day
        focus     = rng.uniform(20, 100, n)       # 20–100
        revision  = rng.integers(0, 8, n).astype(float)  # 0–7 sessions/week
        noise     = rng.normal(0, 5, n)

        score = 20 + 8 * study + 0.4 * focus + 3 * revision + noise
        score = np.clip(score, 0, 100)            # realistic exam score range

        X = np.column_stack([study, focus, revision])
        y = score

        self.pipeline.fit(X, y)
        self._trained = True

    # -----------------------------------------------------------------------
    # Prediction
    # -----------------------------------------------------------------------

    def predict(self, request: SimulationRequest) -> SimulationResponse:
        if not self._trained:
            raise RuntimeError("Prediction engine has not been trained yet.")

        X = np.array([[
            request.study_hours,
            request.focus_score,
            request.revision_frequency,
        ]])

        raw_score       = float(self.pipeline.predict(X)[0])
        clamped_score   = round(min(max(raw_score, 0.0), 100.0), 2)

        return SimulationResponse(
            predicted_score=clamped_score,
            confidence_note=(
                "Score predicted by a Gradient Boosting model trained on synthetic data. "
                "Model uses ensemble learning for better accuracy. "
                "Accuracy improves as real study_log data is used for retraining."
            ),
            input_summary={
                "study_hours":        request.study_hours,
                "focus_score":        request.focus_score,
                "revision_frequency": request.revision_frequency,
            },
        )
