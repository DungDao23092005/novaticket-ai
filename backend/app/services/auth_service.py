"""
services/auth_service.py — Business logic for authentication.

Responsibilities (Service Layer):
    - Orchestrates UserRepository + security utilities
    - Enforces business rules (uniqueness checks, password verification)
    - Routers call service methods — not raw DB queries

Pattern:
    Router → AuthService → UserRepository → DB
    Router → AuthService → security.py (hash, verify, JWT)

AuthService is instantiated per-request with a db Session.
"""

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token, UserRegister


class AuthService:
    """Business logic for user registration and authentication."""

    def __init__(self, db) -> None:
        """
        Args:
            db: SQLAlchemy Session (injected from FastAPI dependency)
        """
        self.repo = UserRepository(db)

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------

    def register(self, data: UserRegister) -> User:
        """
        Register a new user account.

        Business rules:
            1. Email must be unique (case-insensitive)
            2. Username must be unique
            3. Password is hashed before storage — plaintext never persisted

        Args:
            data: Validated UserRegister schema from router

        Returns:
            The newly created User ORM instance

        Raises:
            HTTP 409 Conflict if email or username is already taken
        """
        # Rule 1: Unique email
        if self.repo.exists_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Rule 2: Unique username
        if self.repo.exists_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        # Rule 3: Hash password before storing
        hashed = hash_password(data.password)

        return self.repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hashed,
            full_name=data.full_name,
        )

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> Token:
        """
        Authenticate a user and issue a JWT access token.

        Business rules:
            1. Load user by email — return same error for wrong email OR wrong
               password (prevents user enumeration attacks)
            2. Verify bcrypt password
            3. Check account is active
            4. Issue JWT with user_id as 'sub' claim

        Args:
            email: User's email address
            password: Plaintext password from login request

        Returns:
            Token schema with access_token and token_type

        Raises:
            HTTP 401 if credentials are invalid
            HTTP 403 if account is inactive
        """
        # Load user — same error for wrong email or wrong password
        user = self.repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check account status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        # Issue JWT
        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(access_token=access_token, token_type="bearer")
