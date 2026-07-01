from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db_session
from app.core.dependencies import get_redis
from app.main import app


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session():
        session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        session.execute.return_value = result
        yield session

    async def override_get_redis():
        redis = AsyncMock()
        redis.get.return_value = None
        yield redis

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()
