"""
core/dependencies.py — FastAPI dependency functions.

Dependencies are reusable functions injected into route handlers via Depends().
They handle: database sessions, authentication, authorization.

Current dependencies:
    - get_db: yields a database session per request
    - get_current_user: extracts and validates JWT, returns current User ORM object
    - get_current_active_user: same + checks is_active flag

Usage in routes:
    @router.get("/me")
    def get_me(current_user: User = Depends(get_current_active_user)):
        return current_user
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.user import User

# ----------------------------------------------------------------------
# OAuth2 scheme — tells FastAPI where to find the Bearer token
# tokenUrl must match the login endpoint path
# ----------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/form")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT from the Authorization header.
    Returns the User ORM object for the authenticated user.

    Raises:
        HTTP 401 if:
            - Token is missing (handled by OAuth2PasswordBearer)
            - Token is invalid or expired
            - User ID in token doesn't exist in DB
            - Token payload is malformed (missing 'sub')

    Usage:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Same as get_current_user, but also checks is_active flag.
    Use this for routes that should reject deactivated accounts.

    Raises:
        HTTP 403 if user account is inactive (soft-deleted).

    Usage:
        @router.get("/profile")
        def get_profile(current_user: User = Depends(get_current_active_user)):
            ...
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return current_user
