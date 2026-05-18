"""
app/api/error_handlers.py
──────────────────────────
Registers global exception handlers on the FastAPI app instance.

Ensures ALL error responses follow the standard ErrorResponse schema,
regardless of whether the error is a validation issue, a 404, or an
unhandled server exception. Consistent error shapes make the frontend
much easier to write.
"""

import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_body(error_code: str, message: str, detail=None) -> dict:
    """Consistent error envelope shape."""
    body = {"success": False, "error_code": error_code, "message": message}
    if detail is not None:
        body["detail"] = detail
    return body


def register_error_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the given FastAPI app."""

    # ── 1. Pydantic / FastAPI validation errors ───────────────
    # These fire when the request body fails schema validation.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Build a human-readable list of field errors
        field_errors = []
        for error in exc.errors():
            loc = " → ".join(str(x) for x in error["loc"] if x != "body")
            field_errors.append({"field": loc, "message": error["msg"], "type": error["type"]})

        logger.warning(
            "Request validation failed",
            extra={"path": request.url.path, "errors": field_errors},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                error_code="VALIDATION_ERROR",
                message="One or more input fields are invalid.",
                detail=field_errors,
            ),
        )

    # ── 2. HTTP exceptions (404, 403, 401, etc.) ─────────────
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # exc.detail may already be a structured dict from our routes
        if isinstance(exc.detail, dict):
            body = {"success": False, **exc.detail}
        else:
            code_map = {
                400: "BAD_REQUEST",
                401: "UNAUTHORIZED",
                403: "FORBIDDEN",
                404: "NOT_FOUND",
                405: "METHOD_NOT_ALLOWED",
                409: "CONFLICT",
                422: "UNPROCESSABLE_ENTITY",
                429: "TOO_MANY_REQUESTS",
                500: "INTERNAL_SERVER_ERROR",
                503: "SERVICE_UNAVAILABLE",
            }
            body = _error_body(
                error_code=code_map.get(exc.status_code, "HTTP_ERROR"),
                message=str(exc.detail),
            )

        logger.warning(
            "HTTP exception",
            extra={"status_code": exc.status_code, "path": request.url.path},
        )
        return JSONResponse(status_code=exc.status_code, content=body)

    # ── 3. Unhandled / unexpected exceptions ─────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )

        # In production, hide internal details from the client
        detail = traceback.format_exc() if settings.DEBUG else None

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please try again later.",
                detail=detail,
            ),
        )
