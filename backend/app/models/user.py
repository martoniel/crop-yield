"""
app/models/user.py
──────────────────
SQLAlchemy ORM model for the `users` table.
Stores registered user accounts.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # ── Primary key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # ── Identity ──────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Role / permissions ────────────────────────────────────
    role: Mapped[str] = mapped_column(String(20), default="user")   # "user" | "admin"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────
    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        "Prediction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
