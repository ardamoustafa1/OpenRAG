import httpx
import structlog
from app.core.config import settings
# from email.message import EmailMessage
# import aiosmtplib

logger = structlog.get_logger()

class NotificationService:
    """
    Handles Emails (SMTP/SES) and Webhooks.
    """

    async def send_email(self, to_email: str, subject: str, html_content: str):
        """
        Sends an email using standard SMTP.
        (Placeholder logic until actual SMTP credentials are provided in .env)
        """
        logger.info("Simulating Email send", to_email=to_email, subject=subject)
        
        # Example Implementation:
        # message = EmailMessage()
        # message["From"] = settings.SMTP_FROM_EMAIL
        # message["To"] = to_email
        # message["Subject"] = subject
        # message.add_alternative(html_content, subtype="html")
        # 
        # await aiosmtplib.send(
        #     message,
        #     hostname=settings.SMTP_HOST,
        #     port=settings.SMTP_PORT,
        #     username=settings.SMTP_USER,
        #     password=settings.SMTP_PASSWORD,
        #     use_tls=True
        # )

    async def send_webhook(self, url: str, event_type: str, payload: dict, secret: str = None):
        """
        Dispatches a webhook POST request.
        """
        logger.info("Dispatching Webhook", url=url, event_type=event_type)
        
        data = {
            "event": event_type,
            "data": payload
        }
        
        headers = {"Content-Type": "application/json"}
        if secret:
            # Generate HMAC signature
            import hmac
            import hashlib
            import json
            signature = hmac.new(secret.encode(), json.dumps(data).encode(), hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = signature

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=10.0)
                response.raise_for_status()
                logger.info("Webhook delivered successfully", url=url)
        except Exception as e:
            logger.error("Failed to deliver webhook", url=url, error=str(e))

notification_service = NotificationService()
