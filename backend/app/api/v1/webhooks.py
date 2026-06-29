from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
import structlog

logger = structlog.get_logger()
router = APIRouter(tags=["Webhooks"])

class WebhookCreate(BaseModel):
    url: str
    events: List[str]
    is_active: bool = True
    secret: str

# Mock memory store
MOCK_WEBHOOKS = {}

@router.post("/webhooks", status_code=status.HTTP_201_CREATED)
async def create_webhook(webhook: WebhookCreate):
    """
    Registers a new webhook endpoint for the current tenant.
    Events: document.processed, conversation.created, etc.
    """
    import uuid
    wh_id = str(uuid.uuid4())
    MOCK_WEBHOOKS[wh_id] = webhook.dict()
    logger.info("Webhook created", webhook_id=wh_id, url=webhook.url)
    return {"id": wh_id, **MOCK_WEBHOOKS[wh_id]}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str):
    """
    Fires a dummy event to verify connectivity and signature validation.
    """
    if webhook_id not in MOCK_WEBHOOKS:
        raise HTTPException(status_code=404, detail="Webhook not found")
        
    from app.workers.webhook_sender import send_webhook
    # Trigger celery task asynchronously
    send_webhook.delay(
        webhook_id=webhook_id, 
        event_type="ping", 
        payload={"message": "Test delivery from Enterprise AI Platform"}
    )
    return {"status": "Test event queued"}
