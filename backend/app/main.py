"""
app/main.py
────────────
CropYieldAI — FastAPI Application Entry Point

Responsibilities:
  1. Create the FastAPI app instance
  2. Configure CORS
  3. Register global error handlers
  4. Mount the API router
  5. Manage startup / shutdown lifecycle (DB init, model loading)

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.error_handlers import register_error_handlers
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.base import create_all_tables
from app.ml.loader import initialise_model

# ── Initialise logging as the very first thing ───────────────
setup_logging()
logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# LIFESPAN — startup and shutdown events
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager that runs startup logic before the first request
    and cleanup logic after the last response.
    """
    # ── STARTUP ───────────────────────────────────────────────
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={"environment": settings.APP_ENV},
    )

    # 1. Create database tables (idempotent — safe to run every startup)
    logger.info("Initialising database...")
    await create_all_tables()

    # 2. Load ML model artifacts into memory
    logger.info("Loading ML artifacts...")
    artifacts = initialise_model()

    if artifacts.is_demo:
        logger.warning(
            "⚠️  Running in DEMO mode — no real model files found. "
            "Place model.joblib, scaler.joblib, label_encoders.joblib, "
            "and feature_names.joblib in the trained_models/ directory."
        )
    else:
        logger.info("✅  Production model loaded successfully.")

    logger.info(f"🚀  {settings.APP_NAME} is ready on http://{settings.HOST}:{settings.PORT}")

    yield  # Application is running

    # ── SHUTDOWN ──────────────────────────────────────────────
    logger.info(f"{settings.APP_NAME} shutting down...")


# ─────────────────────────────────────────────────────────────
# APPLICATION FACTORY
# ─────────────────────────────────────────────────────────────
def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "## Crop Yield Prediction API\n\n"
            "Backend API for the CropYieldAI system — a final year computer science project "
            "at Federal University, Dutsin-Ma.\n\n"
            "### Features\n"
            "- ML-powered crop yield prediction (Random Forest Regressor)\n"
            "- Full prediction history with pagination and filtering\n"
            "- JWT-based user authentication\n"
            "- System health monitoring\n\n"
            "### Author\n"
            "**Fayyad Inda Musa** · Department of Computer Science · FUD Dutsin-Ma · 2025"
        ),
        lifespan=lifespan,
        docs_url="/docs",          # Swagger UI
        redoc_url="/redoc",        # ReDoc UI
        openapi_url="/openapi.json",
        contact={
            "name": "Fayyad Inda Musa",
            "email": "fayyad@student.fud.edu.ng",
        },
        license_info={
            "name": "Academic Use Only",
        },
    )

    # ── Middleware ────────────────────────────────────────────

    # CORS — allow frontend dev servers and production origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # ── Error handlers ────────────────────────────────────────
    register_error_handlers(app)

    # ── Routes ────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Root route ────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse({
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "health": "/api/v1/health",
        })

    return app


# ── Create the app instance ───────────────────────────────────
app = create_application()
