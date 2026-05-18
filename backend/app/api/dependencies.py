"""
app/api/dependencies.py
────────────────────────
FastAPI dependency functions shared across routes.

Provides:
  - get_current_user  → extracts and validates the JWT bearer token
  - get_current_admin → same as above, but requires role == "admin"
  - optional_user     → returns user or None (for public-but-auth-aware routes)
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.base import get_db
from app.models.user import User

logger = get_logger(__name__)

# HTTPBearer extracts the "Authorization: Bearer <token>" header automatically
_bearer_scheme = HTTPBearer(auto_error=False)


async def _resolve_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: AsyncSession,
    required: bool,
) -> Optional[User]:
    """
    Internal helper that decodes the JWT and fetches the User from the DB.
    """
    if credentials is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide a Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: requires a valid authenticated user."""
    return await _resolve_user_from_token(credentials, db, required=True)


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: requires authenticated user with role == 'admin'."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required.",
        )
    return current_user


async def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Dependency: returns the authenticated user if a valid token is provided,
    or None for unauthenticated requests. Useful for public endpoints that
    behave differently for logged-in users.
    """
    return await _resolve_user_from_token(credentials, db, required=False)
