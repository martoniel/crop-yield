"""
app/core/config.py
──────────────────
Central configuration module.
All settings are read from environment variables (or .env file).
Pydantic Settings ensures type-safe, validated configuration.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Defaults are safe for local development.
    """

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "CropYieldAI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Server ────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./cropai.db"

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── ML Artifact Paths ────────────────────────────────────
    MODEL_PATH: str = "trained_models/model.joblib"
    SCALER_PATH: str = "trained_models/scaler.joblib"
    ENCODERS_PATH: str = "trained_models/label_encoders.joblib"
    FEATURE_NAMES_PATH: str = "trained_models/feature_names.joblib"

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/cropai.log"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse the comma-separated CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Using lru_cache means we only read .env once per process lifetime.
    """
    return Settings()


# Convenience singleton — import this throughout the app
settings = get_settings()
