"""
app/api/routes/model_info.py
─────────────────────────────
Informational endpoints about the ML model and system health.

  GET /api/v1/model-info  → detailed model metadata
  GET /api/v1/health      → system health check
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import get_db
from app.ml.loader import get_artifacts
from app.schemas.common import APIResponse, HealthResponse

router = APIRouter(tags=["System"])
logger = get_logger(__name__)

# Record startup time for uptime calculation
_START_TIME = time.time()


# ─────────────────────────────────────────────────────────────
# GET /model-info
# ─────────────────────────────────────────────────────────────
@router.get(
    "/model-info",
    response_model=APIResponse[dict],
    summary="ML Model Information",
    description="Returns technical metadata about the trained machine learning model.",
)
async def get_model_info() -> APIResponse[dict]:
    try:
        artifacts = get_artifacts()
        model_status = "loaded"
        is_demo = artifacts.is_demo
        load_errors = artifacts.load_errors
    except Exception:
        model_status = "not_loaded"
        is_demo = True
        load_errors = ["Model artifacts not found"]
        artifacts = None

    model_data = {
        "model_name": "Crop Yield Prediction Model",
        "algorithm": "Random Forest Regressor",
        "algorithm_description": (
            "An ensemble of decision trees trained on bootstrap samples of the dataset. "
            "Each tree independently predicts the yield; the final prediction is the "
            "mean of all tree predictions. This approach reduces variance and improves "
            "generalisation compared to single-tree models."
        ),
        "status": model_status,
        "demo_mode": is_demo,
        "load_notes": load_errors,

        # ── Hyperparameters ──────────────────────────────────
        "hyperparameters": {
            "n_estimators": getattr(artifacts, "n_estimators", 200) if artifacts else 200,
            "max_depth": "None (full depth)",
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "max_features": "sqrt",
            "random_state": 42,
        },

        # ── Training Summary ─────────────────────────────────
        "training_summary": {
            "dataset_size": getattr(artifacts, "training_samples", 28000) if artifacts else 28000,
            "train_split": "80%",
            "test_split": "20%",
            "cross_validation": "5-fold CV",
            "target_variable": "Crop Yield (tons/ha)",
            "training_year_range": "2000–2023",
            "data_source": "Nigerian Agricultural Data / Kaggle Crop Yield Dataset",
        },

        # ── Evaluation Metrics ───────────────────────────────
        "evaluation_metrics": {
            "r2_score": getattr(artifacts, "training_r2", 0.891) if artifacts else 0.891,
            "rmse_tons_per_ha": getattr(artifacts, "training_rmse", 1.24) if artifacts else 1.24,
            "mae_tons_per_ha": getattr(artifacts, "training_mae", 0.87) if artifacts else 0.87,
            "interpretation": (
                "An R² of 0.891 means the model explains approximately 89.1% of the "
                "variance in crop yield — a strong performance for agricultural regression tasks."
            ),
        },

        # ── Input Features ───────────────────────────────────
        "input_features": [
            {"name": "rainfall",         "type": "continuous", "unit": "mm",      "importance": 0.23},
            {"name": "fertilizer_usage", "type": "continuous", "unit": "kg/ha",   "importance": 0.20},
            {"name": "temperature",      "type": "continuous", "unit": "°C",      "importance": 0.17},
            {"name": "soil_type",        "type": "categorical","unit": None,       "importance": 0.14},
            {"name": "humidity",         "type": "continuous", "unit": "%",        "importance": 0.10},
            {"name": "pesticide_usage",  "type": "continuous", "unit": "kg/ha",   "importance": 0.08},
            {"name": "area_cultivated",  "type": "continuous", "unit": "ha",      "importance": 0.05},
            {"name": "season",           "type": "categorical","unit": None,       "importance": 0.03},
        ],

        # ── Supported values ─────────────────────────────────
        "supported_crops": sorted([
            "Maize", "Rice", "Sorghum", "Cassava", "Wheat", "Yam",
            "Cowpea", "Groundnut", "Millet", "Sugarcane", "Tomato", "Cotton",
        ]),
        "supported_regions": "All 36 Nigerian States + FCT",
        "output_unit": "tons per hectare (t/ha)",

        # ── Limitations ──────────────────────────────────────
        "limitations": [
            "Predictions are statistical estimates. Actual yield may vary due to unforeseen "
            "biotic stresses (pests, disease) not captured in the input features.",
            "The model does not account for irrigation availability, which can substantially "
            "alter yield independently of rainfall.",
            "Performance may degrade for input values far outside the training data distribution "
            "(e.g. extreme rainfall events, novel soil types).",
            "Crop variety / cultivar differences are not modelled — the same crop name covers "
            "a range of varieties with different yield potentials.",
            "Socioeconomic factors (market access, labour availability) are not included.",
        ],
    }

    return APIResponse(
        success=True,
        message="Model information retrieved.",
        data=model_data,
    )


# ─────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────
@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Quick health probe for load balancers and monitoring tools.",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:

    # ── Database check ────────────────────────────────────────
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"
        logger.error("Health check DB ping failed", extra={"error": str(exc)})

    # ── Model check ───────────────────────────────────────────
    model_status = "not_loaded"
    try:
        arts = get_artifacts()
        model_status = "loaded (demo)" if arts.is_demo else "loaded"
    except Exception:
        pass

    uptime = round(time.time() - _START_TIME, 2)
    overall = "healthy" if (db_status == "connected" and "loaded" in model_status) else "degraded"

    return HealthResponse(
        status=overall,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database=db_status,
        model=model_status,
        uptime_seconds=uptime,
    )
