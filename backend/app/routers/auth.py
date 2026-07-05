"""
routers/auth.py — Authentication endpoints.

Pattern: Thin router — delegates all business logic to AuthService.
    Router = parse request + call service + return response
    Service = business logic (uniqueness check, password verify, JWT)

Endpoints:
    POST /auth/register     — Register new user account
    POST /auth/login        — Login with JSON body → JWT
    POST /auth/login/form   — Login via OAuth2 form (Swagger UI)
    GET  /auth/me           — Get current authenticated user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import Token, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ----------------------------------------------------------------------
# POST /auth/register
# ----------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    body: UserRegister,
    db: Session = Depends(get_db),
) -> User:
    """
    Register a new user account.

    - **email**: Must be unique and valid email format
    - **username**: Must be unique, 3-50 chars, alphanumeric/underscore/dash
    - **password**: Minimum 8 characters
    - **full_name**: Optional display name

    Returns the created user profile (without password).
    """
    service = AuthService(db)
    return service.register(body)


# ----------------------------------------------------------------------
# POST /auth/login (JSON body — for frontend)
# ----------------------------------------------------------------------
@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password (JSON)",
)
def login(
    body: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """
    Authenticate with email and password.

    Returns a JWT access token:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    service = AuthService(db)
    return service.login(email=body.email, password=body.password)


# ----------------------------------------------------------------------
# POST /auth/login/form (OAuth2 form — for Swagger UI "Authorize" button)
# ----------------------------------------------------------------------
@router.post(
    "/login/form",
    response_model=Token,
    summary="Login via OAuth2 form (for Swagger UI)",
    include_in_schema=True,
)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """
    OAuth2 password flow endpoint for Swagger UI.
    The **username** field should contain the user's **email**.
    """
    service = AuthService(db)
    return service.login(email=form_data.username, password=form_data.password)


# ----------------------------------------------------------------------
# GET /auth/me
# ----------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Returns the profile of the currently authenticated user.

    Requires: `Authorization: Bearer <access_token>` header.
    """
    return current_user
