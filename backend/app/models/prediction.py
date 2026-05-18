"""
app/models/prediction.py
────────────────────────
SQLAlchemy ORM model for the `predictions` table.
Every API call to /predict creates one record here.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    # ── Primary key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Foreign key (optional — nullable for anonymous requests) ─
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Raw input features ────────────────────────────────────
    crop_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    soil_type: Mapped[str] = mapped_column(String(80), nullable=False)
    rainfall: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    fertilizer_usage: Mapped[float] = mapped_column(Float, nullable=False)
    pesticide_usage: Mapped[float] = mapped_column(Float, nullable=False)
    area_cultivated: Mapped[float] = mapped_column(Float, nullable=False)
    season: Mapped[str] = mapped_column(String(40), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Model output ──────────────────────────────────────────
    predicted_yield: Mapped[float] = mapped_column(Float, nullable=False)
    yield_unit: Mapped[str] = mapped_column(String(20), default="tons/ha", nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Audit / metadata ──────────────────────────────────────
    status: Mapped[str] = mapped_column(String(20), default="completed")  # completed | failed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        back_populates="predictions",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} crop={self.crop_name} "
            f"region={self.region} yield={self.predicted_yield}>"
        )
