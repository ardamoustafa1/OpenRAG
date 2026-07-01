import uuid
from typing import Any

import structlog
from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session_factory
from app.models.billing import BillingPlan, TenantSubscription
from app.models.types import RedisClient

logger = structlog.get_logger()


class QuotaStatus:
    def __init__(self, used: int, limit: int) -> None:
        self.used = used
        self.limit = limit
        self.percentage = (used / limit * 100) if limit > 0 else 0
        self.is_exceeded = used >= limit
        self.is_near_limit = self.percentage >= 80


class QuotaManager:
    """
    Manages tenant quotas atomically using Redis INCR.
    """

    def __init__(self) -> None:
        self.redis: RedisClient = Redis.from_url(
            settings.REDIS_URL, decode_responses=True
        )

    async def _get_plan_limits(self, tenant_id: str) -> dict[str, Any]:
        """Fetch the tenant's current billing plan limits."""
        async with async_session_factory() as db:
            try:
                tid_val = uuid.UUID(tenant_id)
            except ValueError:
                return {"tokens": 500_000, "documents": 100, "users": 3}

            stmt = (
                select(BillingPlan)
                .join(TenantSubscription, TenantSubscription.plan_id == BillingPlan.id)
                .where(
                    TenantSubscription.tenant_id == tid_val,
                    TenantSubscription.status == "active",
                )
            )
            plan = (await db.execute(stmt)).scalars().first()
            if not plan:
                # Default limits if no plan found (Free Tier fallback)
                return {"tokens": 500_000, "documents": 100, "users": 3}
            return {
                "tokens": plan.max_tokens_per_month,
                "documents": plan.max_documents,
                "users": plan.max_users,
            }

    async def check_quota(self, tenant_id: str, resource_type: str) -> QuotaStatus:
        """
        Check if a resource (tokens, documents, users) exceeds the limit.
        """
        limits = await self._get_plan_limits(tenant_id)
        limit = limits.get(resource_type, 0)

        # Unlimited
        if limit == -1:
            return QuotaStatus(0, -1)

        cache_key = f"tenant:{tenant_id}:usage:{resource_type}"
        used_raw = await self.redis.get(cache_key)
        used = int(used_raw) if used_raw else 0

        status = QuotaStatus(used, limit)

        if status.is_exceeded:
            logger.warning(
                "Quota exceeded",
                tenant_id=tenant_id,
                resource=resource_type,
                used=used,
                limit=limit,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Quota exceeded for {resource_type}. Please upgrade your plan.",
            )

        return status

    async def record_usage(
        self, tenant_id: str, resource_type: str, amount: int = 1
    ) -> None:
        """
        Atomically increment the usage counter in Redis.
        """
        cache_key = f"tenant:{tenant_id}:usage:{resource_type}"

        # Check quota before incrementing
        status = await self.check_quota(tenant_id, resource_type)

        new_val = await self.redis.incrby(cache_key, amount)

        # Check if we just crossed the 80% or 95% threshold for the first time
        new_percentage = (new_val / status.limit * 100) if status.limit > 0 else 0

        if status.percentage < 80 and new_percentage >= 80:
            # Trigger background warning email via Celery
            from app.workers.scheduled_tasks import trigger_quota_warning

            trigger_quota_warning.delay(tenant_id, resource_type, 80)

        elif status.percentage < 95 and new_percentage >= 95:
            from app.workers.scheduled_tasks import trigger_quota_warning

            trigger_quota_warning.delay(tenant_id, resource_type, 95)

    async def reset_monthly_quotas(self, tenant_id: str) -> None:
        """
        Resets the monthly token and document usage.
        Does NOT reset user count, as that is a hard cap based on active users.
        """
        keys = [
            f"tenant:{tenant_id}:usage:tokens",
            f"tenant:{tenant_id}:usage:documents",
        ]
        await self.redis.delete(*keys)
        logger.info("Monthly quotas reset", tenant_id=tenant_id)


quota_manager = QuotaManager()
