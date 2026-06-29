import pytest
from unittest.mock import AsyncMock

# Mocking a quota service
class QuotaService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.LIMIT = 100

    async def increment_and_check(self, tenant_id: str) -> bool:
        current = await self.redis.incr(f"quota:{tenant_id}")
        return current <= self.LIMIT

@pytest.mark.asyncio
async def test_quota_under_limit():
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 50
    
    service = QuotaService(mock_redis)
    is_allowed = await service.increment_and_check("tenant-1")
    assert is_allowed is True

@pytest.mark.asyncio
async def test_quota_over_limit():
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 101
    
    service = QuotaService(mock_redis)
    is_allowed = await service.increment_and_check("tenant-1")
    assert is_allowed is False
