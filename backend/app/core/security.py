import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from app.core.config import settings

# Setup Argon2 hasher
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate Argon2 hash for password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create a short-lived JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    if isinstance(subject, dict):
        to_encode = subject.copy()
        if "sub" in to_encode:
            to_encode["sub"] = str(to_encode["sub"])
    else:
        to_encode = {"sub": str(subject)}
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create a long-lived JWT refresh token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        # Default 7 days
        expire = datetime.now(UTC) + timedelta(days=7)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_api_key() -> tuple[str, str, str]:
    """
    Generate a secure API key.
    Returns:
        tuple containing: (raw_key, key_hash, key_prefix)
    """
    raw_key = secrets.token_urlsafe(32)
    # Use SHA-256 for API keys to avoid Argon2 overhead on every API request
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    return raw_key, key_hash, key_prefix


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its SHA-256 hashed version."""
    return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key


async def add_token_to_blacklist(redis: Redis, token: str, expires_in: int) -> None:
    """
    Add a token to the Redis blacklist with a TTL.
    Stores the SHA256 hash of the token to save memory and avoid storing full JWTs.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    await redis.setex(f"blacklist:{token_hash}", expires_in, "true")


async def is_token_blacklisted(redis: Redis, token: str) -> bool:
    """
    Check if a token's hash is in the Redis blacklist.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return await redis.exists(f"blacklist:{token_hash}") > 0
