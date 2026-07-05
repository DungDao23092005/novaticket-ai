"""
schemas/user.py — Pydantic schemas for User and Auth.

IMPORTANT SEPARATION:
    ORM Model (app/models/user.py) = Database structure
    Pydantic Schema (this file)     = API input/output contract

Rules:
    - NEVER include hashed_password in any response schema
    - Use `model_config = ConfigDict(from_attributes=True)` to allow
      creating schemas from ORM model instances (SQLAlchemy → Pydantic)
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ----------------------------------------------------------------------
# Request Schemas (Input)
# ----------------------------------------------------------------------

class UserRegister(BaseModel):
    """Schema for POST /auth/register request body."""
    email: EmailStr = Field(
        ...,
        description="Valid email address — used for login",
        examples=["alice@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username (3-50 chars, letters/numbers/underscore/dash only)",
        examples=["alice_123"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
        examples=["MySecurePass123!"],
    )
    full_name: str | None = Field(
        default=None,
        max_length=200,
        description="Optional display name",
        examples=["Alice Nguyen"],
    )


class UserLogin(BaseModel):
    """Schema for POST /auth/login request body (JSON)."""
    email: EmailStr = Field(..., examples=["alice@example.com"])
    password: str = Field(..., examples=["MySecurePass123!"])


# ----------------------------------------------------------------------
# Response Schemas (Output)
# NEVER include hashed_password in response schemas
# ----------------------------------------------------------------------

class UserResponse(BaseModel):
    """Public user profile returned by API endpoints."""
    model_config = ConfigDict(from_attributes=True)  # Allow ORM → Pydantic

    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    created_at: datetime


class UserPublic(BaseModel):
    """Minimal user info shown to other users (no email for privacy)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str | None


# ----------------------------------------------------------------------
# Token Schemas
# ----------------------------------------------------------------------

class Token(BaseModel):
    """Response schema for successful login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from a decoded JWT payload."""
    user_id: int
