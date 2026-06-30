import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.config import settings
from app.core.db import get_db_session
from app.core.dependencies import get_current_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.billing import BillingPlan, TenantSubscription
import structlog

logger = structlog.get_logger()

if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY
else:
    logger.warning("STRIPE_API_KEY is not configured. Billing features will be unavailable.")

def verify_stripe_configured():
    if not settings.STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Billing service is not configured.")

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
    stmt = select(TenantSubscription).where(
        TenantSubscription.tenant_id == tenant.id,
        TenantSubscription.status == "active"
    )
    subscription = (await db.execute(stmt)).scalars().first()
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return subscription

@router.post("/billing/portal", dependencies=[Depends(verify_stripe_configured)])
async def create_stripe_portal(
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Returns a Stripe Customer Portal URL for the user to manage their subscription.
    """
    # Try to find the stripe_customer_id in subscriptions
    stmt = select(TenantSubscription.stripe_customer_id).where(
        TenantSubscription.tenant_id == tenant.id
    ).limit(1)
    stripe_customer_id = (await db.execute(stmt)).scalar_one_or_none()

    if not stripe_customer_id:
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
            stmt = (
                update(TenantSubscription)
                .where(TenantSubscription.stripe_customer_id == customer_id)
                .values(status="canceled")
            )
            await db.execute(stmt)
            await db.commit()
            
        elif event_type == "invoice.paid":
            customer_id = event["data"]["object"]["customer"]
            logger.info("Invoice paid successfully", customer_id=customer_id)
            
            # Extract period end from invoice lines if available, otherwise just log
            lines = event["data"]["object"].get("lines", {}).get("data", [])
            if lines and "period" in lines[0]:
                period_end = datetime.fromtimestamp(lines[0]["period"]["end"], tz=timezone.utc)
                stmt = (
                    update(TenantSubscription)
                    .where(TenantSubscription.stripe_customer_id == customer_id)
                    .values(status="active", current_period_end=period_end)
                )
                await db.execute(stmt)
                await db.commit()
            
        return {"status": "success"}

    except Exception as e:
        logger.error("Stripe webhook handler failed", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Webhook processing error")
