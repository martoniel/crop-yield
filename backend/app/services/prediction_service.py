"""
app/services/prediction_service.py
───────────────────────────────────
Orchestrates the end-to-end prediction pipeline:

  1. Receives a validated PredictionRequest
  2. Calls the preprocessor to transform inputs
  3. Runs model.predict()
  4. Estimates confidence (via tree variance for RandomForest, or fallback)
  5. Persists the result to the database
  6. Returns a PredictionResponse

This service is the single authoritative location for prediction logic.
Routes should not call the ML layer directly.
"""

import math
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PredictionError, ModelNotLoadedError
from app.core.logging import get_logger
from app.ml.loader import get_artifacts
from app.ml.preprocessor import preprocess, build_interpretation
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionRequest, PredictionResponse, InputSummary

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# CONFIDENCE ESTIMATION
# ─────────────────────────────────────────────────────────────
def _estimate_confidence(model, X: np.ndarray) -> float:
    """
    Estimate prediction confidence as a percentage.

    For RandomForestRegressor: compute per-tree predictions and use
    coefficient of variation (lower variance → higher confidence).

    Falls back to a fixed value if the method is not available.
    """
    try:
        if hasattr(model, "estimators_"):
            # Get predictions from each tree in the ensemble
            tree_preds = np.array([tree.predict(X)[0] for tree in model.estimators_])
            mean_pred = tree_preds.mean()
            std_pred  = tree_preds.std()
            if mean_pred == 0:
                return 75.0
            cv = std_pred / abs(mean_pred)  # coefficient of variation
            # Map CV to confidence: low CV → high confidence
            # Empirically: CV < 0.05 → ~95%, CV > 0.4 → ~60%
            confidence = max(50.0, min(98.0, 100 * math.exp(-2.5 * cv)))
            return round(confidence, 2)
    except Exception as exc:
        logger.warning("Confidence estimation failed, using fallback", extra={"error": str(exc)})
    return 80.0


# ─────────────────────────────────────────────────────────────
# MAIN SERVICE FUNCTION
# ─────────────────────────────────────────────────────────────
async def run_prediction(
    request: PredictionRequest,
    db: AsyncSession,
    user_id: Optional[int] = None,
) -> PredictionResponse:
    """
    Full prediction pipeline. Async to allow DB I/O without blocking.

    Args:
        request: Validated PredictionRequest from the route handler.
        db:      Active async database session.
        user_id: Authenticated user ID (None for anonymous requests).

    Returns:
        PredictionResponse with all result fields populated.

    Raises:
        ModelNotLoadedError: If ML artifacts are not available.
        PredictionError:     If the model fails to produce output.
    """

    # ── Step 1: Get artifacts ─────────────────────────────────
    try:
        artifacts = get_artifacts()
    except ModelNotLoadedError:
        logger.error("Prediction attempted but model is not loaded")
        raise

    # ── Step 2: Preprocess input ──────────────────────────────
    logger.info(
        "Starting prediction",
        extra={"crop": request.crop_name, "region": request.region, "user_id": user_id},
    )

    X, feature_names = preprocess(request, artifacts)

    # ── Step 3: Run model.predict() ───────────────────────────
    try:
        if hasattr(artifacts.model, "predict_with_crop"):
            # Demo model accepts crop names directly
            raw_prediction = artifacts.model.predict_with_crop(X, [request.crop_name])
        else:
            raw_prediction = artifacts.model.predict(X)

        predicted_yield = float(round(raw_prediction[0], 3))

        if predicted_yield < 0:
            predicted_yield = 0.0
            logger.warning("Model returned negative yield — clamped to 0.0")

    except Exception as exc:
        logger.exception("Model prediction call failed")
        raise PredictionError(
            "The prediction model failed to generate an output.",
            detail=str(exc),
        ) from exc

    # ── Step 4: Estimate confidence ───────────────────────────
    confidence = _estimate_confidence(artifacts.model, X)

    # ── Step 5: Build interpretation text ─────────────────────
    interpretation = build_interpretation(
        crop=request.crop_name,
        region=request.region,
        season=request.season,
        year=request.year,
        predicted_yield=predicted_yield,
        unit="tons/ha",
        confidence=confidence,
    )

    # ── Step 6: Persist to database ───────────────────────────
    prediction_record = Prediction(
        user_id=user_id,
        crop_name=request.crop_name,
        region=request.region,
        soil_type=request.soil_type,
        rainfall=request.rainfall,
        temperature=request.temperature,
        humidity=request.humidity,
        fertilizer_usage=request.fertilizer_usage,
        pesticide_usage=request.pesticide_usage,
        area_cultivated=request.area_cultivated,
        season=request.season,
        year=request.year,
        predicted_yield=predicted_yield,
        yield_unit="tons/ha",
        confidence_score=confidence,
        model_used=artifacts.algorithm,
        status="completed",
    )
    db.add(prediction_record)
    await db.commit()
    await db.refresh(prediction_record)

    logger.info(
        "Prediction completed and saved",
        extra={
            "prediction_id": prediction_record.id,
            "crop": request.crop_name,
            "yield": predicted_yield,
            "confidence": confidence,
            "demo_mode": artifacts.is_demo,
        },
    )

    # ── Step 7: Build and return response ─────────────────────
    return PredictionResponse(
        prediction_id=prediction_record.id,
        predicted_yield=predicted_yield,
        yield_unit="tons/ha",
        confidence_score=confidence,
        model_used=artifacts.algorithm,
        interpretation=interpretation,
        input_summary=InputSummary(**request.model_dump()),
        timestamp=prediction_record.created_at or datetime.now(timezone.utc),
        status="success",
    )
