"""
app/api/router.py
──────────────────
Master router: aggregates all sub-routers under /api/v1
"""

from fastapi import APIRouter

from app.api.routes import auth, model_info, predict, predictions

api_router = APIRouter(prefix="/api/v1")

# ── Mount sub-routers ────────────────────────────────────────
api_router.include_router(auth.router)          # /api/v1/auth/...
api_router.include_router(predict.router)       # /api/v1/predict
api_router.include_router(predictions.router)   # /api/v1/predictions/...
api_router.include_router(model_info.router)    # /api/v1/model-info  + /api/v1/health
