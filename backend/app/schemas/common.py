"""
app/schemas/common.py
─────────────────────
Shared response envelope and error schemas.
Using a consistent envelope makes the API easier to consume on the frontend.
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope.

    All endpoints return data wrapped in this structure:
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    """
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Standard error response body."""
    success: bool = False
    error_code: str
    message: str
    detail: Optional[Any] = None


class HealthResponse(BaseModel):
    """GET /health response."""
    status: str               # "healthy" | "degraded" | "unhealthy"
    app_name: str
    version: str
    environment: str
    database: str             # "connected" | "error"
    model: str                # "loaded" | "not_loaded"
    uptime_seconds: float
