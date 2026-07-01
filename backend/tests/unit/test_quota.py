import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.quota_manager import QuotaManager, QuotaStatus

pytestmark = pytest.mark.asyncio


async def test_quota_status_properties():
    qs = QuotaStatus(used=50, limit=100)
    assert qs.percentage == 50.0
    assert not qs.is_exceeded
    assert not qs.is_near_limit

    qs_near = QuotaStatus(used=80, limit=100)
    assert qs_near.is_near_limit

    qs_exceeded = QuotaStatus(used=100, limit=100)
    assert qs_exceeded.is_exceeded

    qs_zero_limit = QuotaStatus(used=10, limit=0)
    assert qs_zero_limit.percentage == 0
    assert qs_zero_limit.is_exceeded


async def test_get_plan_limits_invalid_uuid():
    qm = QuotaManager()
    qm.redis = AsyncMock()
    limits = await qm._get_plan_limits("invalid-uuid")
    assert limits == {"tokens": 500_000, "documents": 100, "users": 3}


async def test_get_plan_limits_no_plan():
    qm = QuotaManager()
    qm.redis = AsyncMock()

    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_db

    with patch("app.services.quota_manager.async_session_factory", mock_factory):
        limits = await qm._get_plan_limits(str(uuid.uuid4()))
        assert limits == {"tokens": 500_000, "documents": 100, "users": 3}


async def test_get_plan_limits_with_plan():
    qm = QuotaManager()
    qm.redis = AsyncMock()

    mock_plan = MagicMock()
    mock_plan.max_tokens_per_month = 1_000_000
    mock_plan.max_documents = 500
    mock_plan.max_users = 10

    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_plan
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_db

    with patch("app.services.quota_manager.async_session_factory", mock_factory):
        limits = await qm._get_plan_limits(str(uuid.uuid4()))
        assert limits == {"tokens": 1_000_000, "documents": 500, "users": 10}


async def test_check_quota_unlimited():
    qm = QuotaManager()
    qm.redis = AsyncMock()
    with patch.object(qm, "_get_plan_limits", return_value={"tokens": -1}):
        status = await qm.check_quota("tenant-1", "tokens")
        assert status.limit == -1
        assert status.used == 0


async def test_check_quota_normal_and_exceeded():
    qm = QuotaManager()
    qm.redis = AsyncMock()
    qm.redis.get.return_value = "50"
    with patch.object(qm, "_get_plan_limits", return_value={"tokens": 100}):
        status = await qm.check_quota("tenant-1", "tokens")
        assert status.used == 50
        assert not status.is_exceeded

    qm.redis.get.return_value = "100"
    with patch.object(qm, "_get_plan_limits", return_value={"tokens": 100}):
        with pytest.raises(HTTPException) as exc_info:
            await qm.check_quota("tenant-1", "tokens")
        assert exc_info.value.status_code == 429


async def test_record_usage_and_warning_triggers():
    qm = QuotaManager()
    qm.redis = AsyncMock()

    # 1. Normal increment under threshold
    qm.redis.incrby.return_value = 50
    with patch.object(qm, "check_quota", return_value=QuotaStatus(40, 100)):
        await qm.record_usage("tenant-1", "tokens", 10)
        qm.redis.incrby.assert_called_with("tenant:tenant-1:usage:tokens", 10)

    # 2. Crossing 80% threshold
    qm.redis.incrby.return_value = 80
    with patch.object(qm, "check_quota", return_value=QuotaStatus(70, 100)), patch(
        "app.workers.scheduled_tasks.trigger_quota_warning.delay"
    ) as mock_delay:
        await qm.record_usage("tenant-1", "tokens", 10)
        mock_delay.assert_called_once_with("tenant-1", "tokens", 80)

    # 3. Crossing 95% threshold
    qm.redis.incrby.return_value = 95
    with patch.object(qm, "check_quota", return_value=QuotaStatus(85, 100)), patch(
        "app.workers.scheduled_tasks.trigger_quota_warning.delay"
    ) as mock_delay:
        await qm.record_usage("tenant-1", "tokens", 10)
        mock_delay.assert_called_once_with("tenant-1", "tokens", 95)


async def test_reset_monthly_quotas():
    qm = QuotaManager()
    qm.redis = AsyncMock()
    await qm.reset_monthly_quotas("tenant-1")
    qm.redis.delete.assert_called_once_with(
        "tenant:tenant-1:usage:tokens", "tenant:tenant-1:usage:documents"
    )
