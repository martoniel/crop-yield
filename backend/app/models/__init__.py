"""app/models/__init__.py — expose ORM models for import."""
from app.models.user import User
from app.models.prediction import Prediction

__all__ = ["User", "Prediction"]
