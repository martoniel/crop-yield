"""
app/core/security.py
────────────────────
JWT token creation and verification, password hashing.
Provides helpers used by auth routes and dependencies.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Password hashing ─────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT tokens ───────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict — should include 'sub' (subject / user identifier).
        expires_delta: Override the default expiry window.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug("Access token created", extra={"subject": data.get("sub")})
    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Returns:
        Payload dict if valid, None if expired or invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed", extra={"error": str(exc)})
        return None
