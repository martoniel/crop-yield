"""
app/api/routes/auth.py
───────────────────────
Authentication routes.

  POST /api/v1/auth/register  → create new user account
  POST /api/v1/auth/login     → obtain JWT access token
  GET  /api/v1/auth/me        → get current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    try:
        user = await register_user(payload, db)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "EMAIL_EXISTS", "message": exc.message},
        )

    return APIResponse(
        success=True,
        message="Account created successfully. You can now sign in.",
        data=user,
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="User Login",
    description="Authenticate with email and password. Returns a JWT access token.",
)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    try:
        token_data = await login_user(payload.email, payload.password, db)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return APIResponse(
        success=True,
        message="Login successful.",
        data=token_data,
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Get Current User Profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserResponse]:
    return APIResponse(
        success=True,
        message="User profile retrieved.",
        data=UserResponse.model_validate(current_user),
    )
