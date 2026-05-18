"""
app/schemas/user.py
───────────────────
Pydantic schemas for User registration, login, and token responses.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, examples=["Fayyad Inda Musa"])
    email: EmailStr = Field(..., examples=["fayyad@student.fud.edu.ng"])
    password: str = Field(..., min_length=6, max_length=128, examples=["SecurePass123"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must not be entirely numeric.")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse
