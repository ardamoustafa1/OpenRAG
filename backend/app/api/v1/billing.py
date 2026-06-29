import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db_session
from app.core.dependencies import get_current_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.billing import BillingPlan
import structlog

logger = structlog.get_logger()

# Configure Stripe with API key from settings
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

router = APIRouter(tags=["Billing"])

def verify_tenant_admin(user: User = Depends(get_current_user)):
    if user.role not in ["super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Tenant Admin privileges required")
    return user

@router.get("/billing/current-plan")
async def get_current_plan(
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin)
):
    stmt = select(BillingPlan).where(BillingPlan.tenant_id == tenant.id, BillingPlan.is_active == True)
    plan = (await db.execute(stmt)).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan found")
    return plan

@router.post("/billing/portal")
async def create_stripe_portal(
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin)
):
    """
    Returns a Stripe Customer Portal URL for the user to manage their subscription.
    """
    stripe_customer_id = tenant.settings.get("stripe_customer_id")
    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="Tenant has no linked Stripe customer account")

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url="https://yourplatform.com/admin/billing"
        )
        return {"url": session.url}
    except Exception as e:
        logger.error("Failed to create Stripe portal", error=str(e))
        raise HTTPException(status_code=500, detail="Billing service unavailable")

@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Handles async events from Stripe (e.g. invoice.paid, subscription.deleted).
    Verifies webhook signature using STRIPE_WEBHOOK_SECRET.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook received but STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=503, detail="Billing webhooks not configured")

    payload = await request.body()
    
    try:
        # Verify webhook signature — CRITICAL security check
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError as e:
        logger.warning("Stripe webhook signature verification failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        logger.error("Stripe webhook payload parsing failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")

    try:
        event_type = event.get("type")
        
        if event_type == "customer.subscription.deleted":
            customer_id = event["data"]["object"]["customer"]
            logger.warning("Subscription deleted", customer_id=customer_id)
            # TODO: Find tenant by stripe_customer_id and deactivate plan
            
        elif event_type == "invoice.paid":
            logger.info("Invoice paid successfully")
            # TODO: Update next billing cycle date
            
        return {"status": "success"}

    except Exception as e:
        logger.error("Stripe webhook handler failed", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing error")
