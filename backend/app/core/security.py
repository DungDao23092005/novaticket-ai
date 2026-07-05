"""
core/security.py — Password hashing and JWT token utilities.

Provides:
    - hash_password(plain): bcrypt hash a plaintext password
    - verify_password(plain, hashed): verify password against hash
    - create_access_token(data, expires_delta): create signed JWT
    - decode_access_token(token): decode and validate JWT

Design decisions:
    - bcrypt used DIRECTLY (not via passlib) — passlib 1.7.4 is incompatible
      with bcrypt >= 4.0 which removed the __about__ attribute.
    - bcrypt rounds=12: balance between security (~150ms/hash) and UX
    - JWT algorithm: HS256 (HMAC-SHA256) — symmetric, sufficient for monolith
    - Token subject (sub): string representation of user_id
    - Token expiry: configurable via settings.access_token_expire_minutes

Usage:
    from app.core.security import hash_password, verify_password, create_access_token

    hashed = hash_password("MySecret123")
    ok = verify_password("MySecret123", hashed)
    token = create_access_token({"sub": str(user.id)})
    payload = decode_access_token(token)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt  # noqa: F401 — re-export JWTError for callers

from app.core.config import settings


# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
_BCRYPT_ROUNDS = 12  # 2^12 = 4096 iterations — recommended for 2024+


# ----------------------------------------------------------------------
# Password Hashing (using bcrypt directly, no passlib)
# ----------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        plain_password: The user's plaintext password

    Returns:
        A bcrypt hash string (e.g., "$2b$12$...")
        The hash includes the random salt — no need to store separately.

    Example:
        hashed = hash_password("SecurePass123!")
        # → "$2b$12$eXSq..."
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The password to verify
        hashed_password: The stored bcrypt hash string

    Returns:
        True if the password matches, False otherwise.
        Never raises for wrong password — always returns bool.

    Example:
        verify_password("SecurePass123!", hashed)  # → True
        verify_password("WrongPassword!", hashed)  # → False
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # bcrypt.checkpw raises ValueError for malformed hashes
        # Return False instead of crashing the app
        return False


# ----------------------------------------------------------------------
# JWT Token
# ----------------------------------------------------------------------

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload to encode. Should include "sub" (user identifier as string).
        expires_delta: Optional custom expiry. Defaults to settings.access_token_expire_minutes.

    Returns:
        A signed JWT string.

    Example:
        token = create_access_token({"sub": str(user.id)})
        token = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(hours=24))
    """
    payload = data.copy()

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    payload["exp"] = expire

    token: str = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dict (contains "sub", "exp", etc.)

    Raises:
        jose.JWTError: If the token is invalid, expired, or the signature is wrong.
        The caller should catch JWTError and return HTTP 401.

    Example:
        try:
            payload = decode_access_token(token)
            user_id = int(payload["sub"])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    return payload
