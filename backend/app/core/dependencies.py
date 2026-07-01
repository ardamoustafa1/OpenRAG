from typing import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jwt.exceptions import PyJWTError as JWTError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db_session
from app.core.security import is_token_blacklisted, verify_api_key
from app.models.tenant import Tenant
from app.models.types import RedisClient
from app.models.user import ApiKey, User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False
)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Redis dependency placeholder
async def get_redis() -> AsyncGenerator[RedisClient, None]:
    """Dependency to get Redis client."""
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    api_key_val: str | None = Depends(api_key_header),
    db: AsyncSession = Depends(get_db_session),
    redis: RedisClient = Depends(get_redis),
) -> User:
    """
    Validate the token or API key and return the current active User.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user: User | None = None

    # 1. API Key Auth
    if api_key_val:
        # Expected format: "prefix.raw_key"
        parts = api_key_val.split(".", 1)
        if len(parts) == 2:
            prefix, raw_key = parts
            stmt = select(ApiKey).where(
                ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True)
            )
            result = await db.execute(stmt)
            api_key_obj = result.scalars().first()
            if api_key_obj and verify_api_key(api_key_val, api_key_obj.key_hash):
                # Retrieve user associated with the API key
                user_stmt = select(User).where(
                    User.id == api_key_obj.user_id, User.is_active.is_(True)
                )
                user = (await db.execute(user_stmt)).scalars().first()

    # 2. JWT Auth
    elif token:
        if await is_token_blacklisted(redis, token):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: str | None = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            token_type = payload.get("type")
            if token_type != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
        except JWTError:
            raise credentials_exception from None

        user_stmt = select(User).where(User.id == user_id)
        user = (await db.execute(user_stmt)).scalars().first()

    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    requested_tenant_id = request.headers.get("X-Tenant-ID")
    if requested_tenant_id and requested_tenant_id != str(user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to requested tenant",
        )

    # Attach to request state for middlewares to access
    request.state.user_id = user.id
    request.state.tenant_id = user.tenant_id
    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Tenant:
    """Get the active tenant associated with the current user."""
    stmt = select(Tenant).where(Tenant.id == current_user.tenant_id)
    tenant = (await db.execute(stmt)).scalars().first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive or not found")
    return tenant


class RoleChecker:
    """Dependency class to check user roles."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role",
            )
        return user


def require_role(roles: list[str]) -> RoleChecker:
    """Returns a dependency that checks if the user has one of the required roles."""
    return RoleChecker(roles)
