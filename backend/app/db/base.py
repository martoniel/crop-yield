"""
app/db/base.py
──────────────
Async SQLAlchemy engine, session factory, and base declarative model.
All ORM models inherit from `Base`.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Engine ────────────────────────────────────────────────────
# connect_args is required for SQLite to allow cross-thread usage in async context.
_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,           # Log SQL statements in development
    connect_args=_connect_args,
    pool_pre_ping=True,            # Verify connections before use
)

# ── Session factory ───────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # Keep attributes accessible after commit
    autoflush=False,
    autocommit=False,
)

# ── Declarative base ──────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── Dependency ────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.
    Ensures the session is always closed, even on errors.

    Usage in route:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Startup helpers ───────────────────────────────────────────
async def create_all_tables() -> None:
    """Create all registered ORM tables if they do not already exist."""
    async with engine.begin() as conn:
        # Import models here so Base.metadata is populated
        from app.models import prediction, user  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created")


async def drop_all_tables() -> None:
    """Drop all tables — for testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables dropped")
