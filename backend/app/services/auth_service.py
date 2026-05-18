"""
app/services/auth_service.py
─────────────────────────────
Handles user registration and authentication logic.
Separates business rules from the route layer.
"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserRegisterRequest, UserResponse

logger = get_logger(__name__)


async def register_user(data: UserRegisterRequest, db: AsyncSession) -> UserResponse:
    """
    Create a new user account.

    Raises:
        AuthenticationError: If the email is already registered.
    """
    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise AuthenticationError(
            "Email already registered.",
            detail=f"An account with email '{data.email}' already exists.",
        )

    user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("New user registered", extra={"user_id": user.id, "email": user.email})
    return UserResponse.model_validate(user)


async def login_user(email: str, password: str, db: AsyncSession) -> TokenResponse:
    """
    Validate credentials and issue a JWT access token.

    Raises:
        AuthenticationError: On invalid email, password, or inactive account.
    """
    result = await db.execute(select(User).where(User.email == email))
    user: User | None = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Failed login attempt", extra={"email": email})
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated. Contact support.")

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=expires,
    )

    logger.info("User logged in", extra={"user_id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(expires.total_seconds()),
        user=UserResponse.model_validate(user),
    )
