import structlog
from fastapi import APIRouter, Response, status
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.core.db import async_session_factory
from app.rag.vector_store import vector_store
from app.services.storage import storage_service

logger = structlog.get_logger()
router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_liveness():
    """Fast liveness probe for Kubernetes."""
    return {"status": "ok"}


@router.get("/ready")
async def health_readiness(response: Response):
    """Deep readiness probe checking all critical dependencies."""
    components = {"postgres": False, "redis": False, "qdrant": False, "minio": False}

    # 1. Check Postgres
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
            components["postgres"] = True
    except Exception as e:
        logger.error("Postgres readiness check failed", error=str(e))

    # 2. Check Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        if await redis.ping():
            components["redis"] = True
        await redis.close()
    except Exception as e:
        logger.error("Redis readiness check failed", error=str(e))

    # 3. Check Qdrant
    try:
        if await vector_store.client.get_collections():
            components["qdrant"] = True
    except Exception as e:
        logger.error("Qdrant readiness check failed", error=str(e))

    # 4. Check MinIO
    try:
        if storage_service.client.bucket_exists(storage_service.bucket_name):
            components["minio"] = True
    except Exception as e:
        logger.error("MinIO readiness check failed", error=str(e))

    # Determine overall status
    is_ready = all(components.values())

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ready" if is_ready else "degraded", "components": components}
