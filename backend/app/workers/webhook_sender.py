import hashlib
import hmac
import json
from typing import Any

import httpx
import structlog
from celery import Celery

logger = structlog.get_logger()

# Mock Celery App
celery_app = Celery("webhook_worker", broker="redis://localhost:6379/0")


def generate_signature(secret: str, payload: dict[str, Any]) -> str:
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    return hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()


@celery_app.task(bind=True, max_retries=5, retry_backoff=True, retry_backoff_max=600)  # type: ignore[untyped-decorator]
def send_webhook(
    self: Any, webhook_id: str, event_type: str, payload: dict[str, Any]
) -> str:
    """
    Delivers a webhook payload with exponential backoff on 5xx errors.
    Signs the payload using HMAC-SHA256 for verification by the receiver.
    """
    # In a real app, query DB for webhook URL and Secret
    mock_url = "https://example.com/webhook-receiver"
    mock_secret = "whsec_supersecret_key"

    full_payload = {"event": event_type, "data": payload}

    signature = generate_signature(mock_secret, full_payload)
    headers = {
        "Content-Type": "application/json",
        "X-Platform-Signature": signature,
        "X-Webhook-ID": webhook_id,
    }

    try:
        response = httpx.post(
            mock_url, json=full_payload, headers=headers, timeout=10.0
        )

        if 200 <= response.status_code < 300:
            logger.info(
                "Webhook delivered successfully",
                webhook_id=webhook_id,
                status=response.status_code,
            )
            return "Success"
        elif 400 <= response.status_code < 500:
            logger.error(
                "Webhook delivery failed (Client Error). Won't retry.",
                webhook_id=webhook_id,
                status=response.status_code,
                response=response.text,
            )
            return "Failed - No Retry"
        else:
            logger.warning(
                "Webhook delivery failed (Server Error). Retrying...",
                webhook_id=webhook_id,
                status=response.status_code,
            )
            raise self.retry(exc=Exception(f"Server returned {response.status_code}"))

    except httpx.RequestError as exc:
        logger.warning(
            "Webhook delivery network error. Retrying...",
            webhook_id=webhook_id,
            error=str(exc),
        )
        raise self.retry(exc=exc) from exc
