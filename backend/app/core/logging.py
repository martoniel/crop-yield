"""
app/core/logging.py
───────────────────
Configures structured logging for the application.
In development: human-readable console output.
In production: JSON-formatted logs suitable for log aggregators.
"""

import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure root logger with appropriate handlers and formatters.
    Called once at application startup.
    """

    # Ensure log directory exists
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # ── Root logger ──────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    # ── Console handler ──────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.is_production:
        # JSON format for production (parseable by log aggregators)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        # Readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ── File handler ─────────────────────────────────────────
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info(
        "Logging initialised",
        extra={"app": settings.APP_NAME, "env": settings.APP_ENV, "level": settings.LOG_LEVEL},
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use this in every module."""
    return logging.getLogger(name)
