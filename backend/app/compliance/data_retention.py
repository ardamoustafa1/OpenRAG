import datetime

import structlog
from sqlalchemy import delete

from app.core.db import async_session_factory
from app.models.chat import Message
from app.models.log import AuditLog

logger = structlog.get_logger()


async def enforce_retention_policies():
    """
    Cron job triggered by Celery Beat.
    Hard deletes data older than tenant-specific or legal thresholds.
    """
    logger.info("Starting Data Retention Policy Enforcement")

    two_years_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=365 * 2
    )
    five_years_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=365 * 5
    )

    async with async_session_factory() as db:
        # 1. Delete Messages older than 2 years
        msg_stmt = delete(Message).where(Message.created_at < two_years_ago)
        res = await db.execute(msg_stmt)
        logger.info(f"Deleted {res.rowcount} messages older than 2 years.")

        # 2. Delete Audit Logs older than 5 years (Legal requirement)
        audit_stmt = delete(AuditLog).where(AuditLog.created_at < five_years_ago)
        res2 = await db.execute(audit_stmt)
        logger.info(f"Deleted {res2.rowcount} audit logs older than 5 years.")

        await db.commit()
