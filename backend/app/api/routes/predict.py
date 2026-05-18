"""
app/api/routes/predict.py
──────────────────────────
POST /api/v1/predict

Accepts agricultural parameters, runs the ML pipeline,
persists the result, and returns a structured prediction response.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import optional_user
from app.core.exceptions import ModelNotLoadedError, PredictionError, PreprocessingError
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import run_prediction

router = APIRouter(prefix="/predict", tags=["Prediction"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=APIResponse[PredictionResponse],
    status_code=status.HTTP_200_OK,
    summary="Run Crop Yield Prediction",
    description=(
        "Submit agricultural and environmental parameters to receive a "
        "machine learning-generated crop yield estimate. "
        "Authentication is optional — authenticated users have predictions "
        "linked to their account history."
    ),
)
async def predict_crop_yield(
    payload: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
) -> APIResponse[PredictionResponse]:
    """
    Main prediction endpoint.

    - **crop_name**: One of the supported Nigerian crops
    - **region**: Nigerian state or FCT
    - **soil_type**: Dominant field soil classification
    - **rainfall**: Seasonal/annual rainfall in mm
    - **temperature**: Average temperature in °C
    - **humidity**: Relative humidity in %
    - **fertilizer_usage**: Total fertilizer in kg/ha
    - **pesticide_usage**: Total pesticide in kg/ha
    - **area_cultivated**: Farm area in hectares
    - **season**: Wet / Dry / Rabi / Kharif
    - **year**: Prediction year (2000–2100)
    """
    user_id = current_user.id if current_user else None

    try:
        result = await run_prediction(
            request=payload,
            db=db,
            user_id=user_id,
        )
    except ModelNotLoadedError as exc:
        logger.error("Model not loaded during prediction request")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "MODEL_NOT_LOADED",
                "message": "The prediction model is currently unavailable.",
                "detail": exc.detail,
            },
        )
    except PreprocessingError as exc:
        logger.warning("Preprocessing failed", extra={"detail": exc.detail})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "PREPROCESSING_FAILED",
                "message": exc.message,
                "detail": exc.detail,
            },
        )
    except PredictionError as exc:
        logger.error("Prediction pipeline error", extra={"detail": exc.detail})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PREDICTION_FAILED",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    return APIResponse(
        success=True,
        message="Crop yield prediction generated successfully.",
        data=result,
    )
