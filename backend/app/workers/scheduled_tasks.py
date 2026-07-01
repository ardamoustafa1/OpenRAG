import asyncio

import structlog
from sqlalchemy import select

from app.core.db import async_session_factory
from app.models.tenant import Tenant
from app.services.notification import notification_service
from app.services.quota_manager import quota_manager
from app.workers.celery_app import celery_app

logger = structlog.get_logger()

# Async Helper Functions


async def _reset_monthly_quotas() -> None:
    logger.info("Starting monthly quota reset job")
    async with async_session_factory() as db:
        stmt = select(Tenant.id).where(Tenant.is_active.is_(True))
        result = await db.execute(stmt)
        tenant_ids = result.scalars().all()

        for tid in tenant_ids:
            await quota_manager.reset_monthly_quotas(str(tid))
    logger.info("Finished monthly quota reset job")


async def _trigger_quota_warning(
    tenant_id: str, resource_type: str, percentage: int
) -> None:
    # In a real scenario, fetch tenant admin email from DB
    admin_email = "admin@example.com"

    subject = f"ACTION REQUIRED: Quota Warning ({percentage}%)"
    html_content = f"Your tenant has used {percentage}% of its allocated {resource_type}. Please upgrade your plan to avoid service interruption."

    await notification_service.send_email(
        to_email=admin_email, subject=subject, html_content=html_content
    )


# Celery Tasks


@celery_app.task(name="app.workers.scheduled_tasks.reset_monthly_quotas_task")  # type: ignore[untyped-decorator]
def reset_monthly_quotas_task() -> None:
    asyncio.run(_reset_monthly_quotas())


@celery_app.task(name="app.workers.scheduled_tasks.send_usage_summary_emails_task")  # type: ignore[untyped-decorator]
def send_usage_summary_emails_task() -> None:
    # Implementation for daily usage summary
    logger.info("Sending daily usage summaries...")
    # asyncio.run(...)


@celery_app.task(name="app.workers.scheduled_tasks.trigger_quota_warning")  # type: ignore[untyped-decorator]
def trigger_quota_warning(tenant_id: str, resource_type: str, percentage: int) -> None:
    logger.info("Triggering quota warning", tenant_id=tenant_id, percentage=percentage)
    asyncio.run(_trigger_quota_warning(tenant_id, resource_type, percentage))
