"""
app/api/routes/predictions.py
───────────────────────────────
CRUD endpoints for stored prediction records.

  GET    /api/v1/predictions          → paginated history list
  GET    /api/v1/predictions/{id}     → single record
  DELETE /api/v1/predictions/{id}     → delete a record
  GET    /api/v1/predictions/stats    → aggregate analytics
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, optional_user
from app.core.exceptions import RecordNotFoundError
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.prediction import PredictionList, PredictionRecord

router = APIRouter(prefix="/predictions", tags=["Prediction History"])
logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# GET /predictions  — paginated list
# ─────────────────────────────────────────────────────────────
@router.get(
    "",
    response_model=APIResponse[PredictionList],
    summary="List Prediction History",
    description="Returns a paginated list of past predictions. "
                "Authenticated users see only their own records. "
                "Admin users see all records.",
)
async def list_predictions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    crop_name: Optional[str] = Query(None, description="Filter by crop name"),
    region: Optional[str] = Query(None, description="Filter by region/state"),
    season: Optional[str] = Query(None, description="Filter by season"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
) -> APIResponse[PredictionList]:

    query = select(Prediction).order_by(Prediction.created_at.desc())

    # Non-admin authenticated users see only their own predictions
    if current_user and current_user.role != "admin":
        query = query.where(Prediction.user_id == current_user.id)

    # Apply optional filters
    if crop_name:
        query = query.where(Prediction.crop_name.ilike(f"%{crop_name}%"))
    if region:
        query = query.where(Prediction.region.ilike(f"%{region}%"))
    if season:
        query = query.where(Prediction.season == season)

    # Total count (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    records = result.scalars().all()

    return APIResponse(
        success=True,
        message=f"Retrieved {len(records)} prediction records.",
        data=PredictionList(
            total=total,
            page=page,
            page_size=page_size,
            results=[PredictionRecord.model_validate(r) for r in records],
        ),
    )


# ─────────────────────────────────────────────────────────────
# GET /predictions/stats  — aggregate analytics
# ─────────────────────────────────────────────────────────────
@router.get(
    "/stats",
    response_model=APIResponse[dict],
    summary="Prediction Analytics",
    description="Returns aggregate statistics across prediction records.",
)
async def prediction_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
) -> APIResponse[dict]:

    base_filter = []
    if current_user and current_user.role != "admin":
        base_filter.append(Prediction.user_id == current_user.id)

    # Total count
    total_q = await db.execute(
        select(func.count(Prediction.id)).where(*base_filter)
    )
    total = total_q.scalar_one()

    # Average yield
    avg_q = await db.execute(
        select(func.avg(Prediction.predicted_yield)).where(*base_filter)
    )
    avg_yield = avg_q.scalar_one()

    # Most predicted crop
    crop_q = await db.execute(
        select(Prediction.crop_name, func.count(Prediction.crop_name).label("cnt"))
        .where(*base_filter)
        .group_by(Prediction.crop_name)
        .order_by(func.count(Prediction.crop_name).desc())
        .limit(1)
    )
    top_crop_row = crop_q.first()
    top_crop = top_crop_row[0] if top_crop_row else None

    # Most active region
    region_q = await db.execute(
        select(Prediction.region, func.count(Prediction.region).label("cnt"))
        .where(*base_filter)
        .group_by(Prediction.region)
        .order_by(func.count(Prediction.region).desc())
        .limit(1)
    )
    top_region_row = region_q.first()
    top_region = top_region_row[0] if top_region_row else None

    # Max and min yields
    minmax_q = await db.execute(
        select(func.min(Prediction.predicted_yield), func.max(Prediction.predicted_yield))
        .where(*base_filter)
    )
    min_yield, max_yield = minmax_q.first() or (None, None)

    return APIResponse(
        success=True,
        message="Statistics computed successfully.",
        data={
            "total_predictions": total,
            "average_yield_tons_per_ha": round(avg_yield, 3) if avg_yield else None,
            "min_yield_tons_per_ha": round(min_yield, 3) if min_yield else None,
            "max_yield_tons_per_ha": round(max_yield, 3) if max_yield else None,
            "most_predicted_crop": top_crop,
            "most_active_region": top_region,
        },
    )


# ─────────────────────────────────────────────────────────────
# GET /predictions/{id}  — single record
# ─────────────────────────────────────────────────────────────
@router.get(
    "/{prediction_id}",
    response_model=APIResponse[PredictionRecord],
    summary="Get Single Prediction",
)
async def get_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
) -> APIResponse[PredictionRecord]:

    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    record: Optional[Prediction] = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "NOT_FOUND",
                "message": f"Prediction with id={prediction_id} does not exist.",
            },
        )

    # Users can only view their own predictions (unless admin)
    if (
        current_user
        and current_user.role != "admin"
        and record.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "Access denied."},
        )

    return APIResponse(
        success=True,
        message="Prediction record retrieved.",
        data=PredictionRecord.model_validate(record),
    )


# ─────────────────────────────────────────────────────────────
# DELETE /predictions/{id}
# ─────────────────────────────────────────────────────────────
@router.delete(
    "/{prediction_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete a Prediction Record",
)
async def delete_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict]:

    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    record: Optional[Prediction] = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Prediction id={prediction_id} not found."},
        )

    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "You cannot delete another user's prediction."},
        )

    await db.execute(delete(Prediction).where(Prediction.id == prediction_id))
    await db.commit()

    logger.info("Prediction deleted", extra={"prediction_id": prediction_id, "by_user": current_user.id})

    return APIResponse(
        success=True,
        message=f"Prediction id={prediction_id} deleted successfully.",
        data={"deleted_id": prediction_id},
    )
