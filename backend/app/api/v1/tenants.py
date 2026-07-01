import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.dependencies import get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.services.tenant_provisioner import tenant_provisioner

router = APIRouter(tags=["Super Admin (Tenants)"])


def verify_super_admin(user: User = Depends(get_current_user)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin privileges required")
    return user


class TenantCreateSchema(BaseModel):
    name: str
    slug: str
    admin_email: EmailStr
    plan: str = "starter"


@router.post("/tenants")
async def create_tenant(
    data: TenantCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(verify_super_admin),
):
    """Provisions a new tenant ecosystem."""
    # Check if slug exists
    stmt = select(Tenant).where(Tenant.slug == data.slug)
    if (await db.execute(stmt)).scalars().first():
        raise HTTPException(status_code=400, detail="Tenant slug already exists")

    tenant = await tenant_provisioner.provision_tenant(
        db=db,
        name=data.name,
        slug=data.slug,
        admin_email=data.admin_email,
        plan_name=data.plan,
    )
    return tenant


@router.get("/tenants")
async def list_tenants(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(verify_super_admin),
):
    stmt = select(Tenant)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(verify_super_admin),
):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.is_active = False
    await db.commit()
    return {"message": "Tenant suspended"}


@router.post("/tenants/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(verify_super_admin),
):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.is_active = True
    await db.commit()
    return {"message": "Tenant reactivated"}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: uuid.UUID,
    hard_delete: bool = False,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(verify_super_admin),
):
    """
    Soft deletes or hard deletes a tenant.
    Hard delete destroys data in MinIO and Qdrant permanently.
    """
    await tenant_provisioner.deprovision_tenant(db, tenant_id, hard_delete=hard_delete)
    return {
        "message": f"Tenant {'hard' if hard_delete else 'soft'} deleted successfully"
    }


@router.post("/tenants/{tenant_id}/impersonate")
async def impersonate_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(verify_super_admin),
):
    """
    Returns an access token allowing the Super Admin to act as a Tenant Admin.
    """
    # In a real app, generate a JWT specifically flagged as 'impersonated'
    from app.core.security import create_access_token

    # Find the tenant admin
    stmt = select(User).where(User.tenant_id == tenant_id, User.role == "tenant_admin")
    tenant_admin = (await db.execute(stmt)).scalars().first()

    if not tenant_admin:
        raise HTTPException(
            status_code=404, detail="No tenant admin found for this tenant"
        )

    token = create_access_token(subject=str(tenant_admin.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "impersonated_user": tenant_admin.email,
    }
