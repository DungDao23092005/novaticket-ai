"""
routers/auth.py — Authentication endpoints.

Endpoints:
    POST /auth/register     — Register new user account (JSON body)
    POST /auth/login        — Login and receive JWT (JSON body)
    POST /auth/login/form   — Login via OAuth2 form (for Swagger UI)
    GET  /auth/me           — Get current authenticated user profile

Design notes:
    - register: check email/username uniqueness before insert
    - login: load user by email → verify password → issue JWT
    - Two login endpoints: JSON (for frontend) + form (for Swagger UI)
    - /auth/me: protected route to verify auth is working
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import Token, UserLogin, UserRegister, UserResponse

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
    # Check email uniqueness
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check username uniqueness
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # Create user
    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


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

    Returns a JWT access token to use in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    # Load user by email
    user = db.query(User).filter(User.email == body.email).first()

    # Verify password (same error for wrong email or wrong password — prevent enumeration)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Issue JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, token_type="bearer")


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
    OAuth2 password flow endpoint.
    Used by Swagger UI's "Authorize" button.
    Username field should contain the user's **email**.
    """
    # OAuth2 form uses "username" field — we treat it as email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


# ----------------------------------------------------------------------
# GET /auth/me — Protected route: verify auth is working
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
