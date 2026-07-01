from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "enterprise_rag_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.ingestion_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Acknowledge tasks only when they finish executing, not when they are fetched
    task_acks_late=True,
    # Reject the task so it gets re-queued if worker crashes
    task_reject_on_worker_lost=True,
)

celery_app.conf.beat_schedule = {
    "reset-monthly-quotas-1st-of-month": {
        "task": "app.workers.scheduled_tasks.reset_monthly_quotas_task",
        "schedule": crontab(0, 0, day_of_month="1"),
    },
    "send-usage-summary-emails-daily": {
        "task": "app.workers.scheduled_tasks.send_usage_summary_emails_task",
        "schedule": crontab(0, 8, "*"),
    },
}
