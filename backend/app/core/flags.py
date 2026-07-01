import json
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


class FeatureFlags:
    """
    Lightweight Feature Flag service backed by Redis.
    Allows enabling/disabling features globally or per-tenant.
    """

    def __init__(self):
        # We will initialize this with the actual Redis connection pool
        self.redis = None

    def init_app(self, redis_client: Any):
        self.redis = redis_client

    async def is_enabled(
        self, feature_name: str, tenant_id: UUID | str = None, default: bool = False
    ) -> bool:
        """
        Check if a feature is enabled.
        Checks tenant-specific flag first, then falls back to global flag.
        """
        if not self.redis:
            logger.warning(
                "Feature flags checking without Redis initialized. Returning default."
            )
            return default

        try:
            # 1. Check tenant override
            if tenant_id:
                tenant_flag = await self.redis.get(
                    f"ff:tenant:{tenant_id}:{feature_name}"
                )
                if tenant_flag is not None:
                    return json.loads(tenant_flag)

            # 2. Check global flag
            global_flag = await self.redis.get(f"ff:global:{feature_name}")
            if global_flag is not None:
                return json.loads(global_flag)

        except Exception as e:
            logger.error("Error reading feature flag from Redis", error=str(e))

        return default

    async def set_global_flag(self, feature_name: str, value: bool):
        if self.redis:
            await self.redis.set(f"ff:global:{feature_name}", json.dumps(value))

    async def set_tenant_flag(
        self, feature_name: str, tenant_id: UUID | str, value: bool
    ):
        if self.redis:
            await self.redis.set(
                f"ff:tenant:{tenant_id}:{feature_name}", json.dumps(value)
            )


# Global instance
flags = FeatureFlags()
