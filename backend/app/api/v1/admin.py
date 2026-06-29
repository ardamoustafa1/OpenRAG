from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db_session
from app.core.dependencies import get_current_tenant, get_current_user, get_redis
from app.models.tenant import Tenant
from app.models.user import User
from app.models.document import Document
from app.models.chat import Conversation
from app.services.quota_manager import quota_manager

router = APIRouter(tags=["Tenant Admin"])

def verify_tenant_admin(user: User = Depends(get_current_user)):
    if user.role not in ["super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Tenant Admin privileges required")
    return user

@router.get("/admin/dashboard")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin),
    redis: Redis = Depends(get_redis)
):
    """Returns aggregated metrics for the Tenant Admin Dashboard."""
    
    # User Count
    user_count = await db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant.id))
    
    # Document Count
    doc_count = await db.scalar(select(func.count(Document.id)).where(Document.tenant_id == tenant.id))
    
    # Conversation Count
    chat_count = await db.scalar(select(func.count(Conversation.id)).where(Conversation.tenant_id == tenant.id))
    
    # Usage (from Redis)
    tokens_used = await redis.get(f"tenant:{tenant.id}:usage:tokens")
    
    return {
        "users": user_count or 0,
        "documents": doc_count or 0,
        "conversations": chat_count or 0,
        "tokens_used_this_month": int(tokens_used) if tokens_used else 0
    }

@router.get("/admin/settings")
async def get_settings(
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin)
):
    return {"settings": tenant.settings}

@router.patch("/admin/settings")
async def update_settings(
    settings_update: dict,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin)
):
    # Merge existing settings with updates
    current = tenant.settings or {}
    current.update(settings_update)
    
    tenant.settings = current
    await db.commit()
    
    return {"message": "Settings updated", "settings": tenant.settings}

@router.post("/admin/settings/webhook")
async def register_webhook(
    url: str,
    secret: str,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin)
):
    """Saves webhook config to tenant settings."""
    settings = tenant.settings or {}
    settings["webhook"] = {
        "url": url,
        "secret": secret
    }
    tenant.settings = settings
    await db.commit()
    
    # Fire a test webhook event async
    from app.services.notification import notification_service
    import asyncio
    asyncio.create_task(
        notification_service.send_webhook(url, "ping", {"message": "Webhook configured successfully"}, secret)
    )
    
    return {"message": "Webhook registered and ping event dispatched"}

@router.get("/admin/usage")
async def get_detailed_usage(
    tenant: Tenant = Depends(get_current_tenant),
    admin: User = Depends(verify_tenant_admin)
):
    """Returns quota limits vs current usage."""
    token_status = await quota_manager.check_quota(str(tenant.id), "tokens")
    doc_status = await quota_manager.check_quota(str(tenant.id), "documents")
    user_status = await quota_manager.check_quota(str(tenant.id), "users")
    
    return {
        "tokens": {"used": token_status.used, "limit": token_status.limit, "percentage": token_status.percentage},
        "documents": {"used": doc_status.used, "limit": doc_status.limit, "percentage": doc_status.percentage},
        "users": {"used": user_status.used, "limit": user_status.limit, "percentage": user_status.percentage}
    }
