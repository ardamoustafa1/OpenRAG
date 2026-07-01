from contextvars import ContextVar
from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Global ContextVar for tenant_id. Can be set by a middleware and accessed globally
# if we do not want to pass request all the way down, but passing through Dependency is better.
current_tenant_id_var: ContextVar[str | None] = ContextVar(
    "current_tenant_id", default=None
)

# Create the async engine with connection pooling parameters as requested
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
    pool_size=5,  # min_size = 5 (SQLAlchemy handles this via pool_size essentially)
    max_overflow=15,  # max_size = 20 (pool_size + max_overflow)
    pool_timeout=30,  # timeout = 30
    pool_pre_ping=True,
)

# Async session maker factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency to yield a database session.
    Automatically applies Row-Level Security (RLS) if tenant_id is found in the request.

    In a real app, you would extract the tenant_id from the authenticated user's JWT
    or an X-Tenant-ID header verified against their permissions.
    """
    # Placeholder: Extract tenant_id from request.state or headers
    # e.g., tenant_id = request.state.user.tenant_id
    tenant_id = getattr(request.state, "tenant_id", None)

    # Or for testing, check a header directly
    if not tenant_id:
        tenant_id = request.headers.get("X-Tenant-ID")

    async with async_session_factory() as session:
        if tenant_id:
            # Set the tenant_id for RLS within this session transaction
            await session.execute(
                text("SET LOCAL app.current_tenant_id = :tenant_id"),
                {"tenant_id": str(tenant_id)},
            )

            # Optional: Set user_id for Audit Log triggers
            user_id = getattr(request.state, "user_id", None) or request.headers.get(
                "X-User-ID"
            )
            if user_id:
                await session.execute(
                    text("SET LOCAL app.current_user_id = :user_id"),
                    {"user_id": str(user_id)},
                )

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Session is closed, connections returned to pool.
            # Using SET LOCAL ensures variables are cleared when the transaction ends.
            pass
