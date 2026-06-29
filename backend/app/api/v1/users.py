from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.db import get_db_session
from app.core.dependencies import get_current_user, require_role, get_current_tenant
from app.schemas.users import UserCreate, UserUpdate, UserResponse
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import get_password_hash, create_access_token

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["super_admin", "tenant_admin"])),
    tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """List all users within the tenant."""
    # RLS ensures we only see users for this tenant
    stmt = select(User).where(User.deleted_at == None)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["super_admin", "tenant_admin"])),
    tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Create a new user (invitation)."""
    # Check if exists
    stmt = select(User).where(User.email == user_in.email)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        tenant_id=tenant.id,
        email=user_in.email,
        name=user_in.name,
        role=user_in.role,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/{user_id}/impersonate")
async def impersonate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["super_admin"]))
) -> Any:
    """
    Allows a super_admin to generate an access token as another user.
    Extremely sensitive.
    """
    stmt = select(User).where(User.id == user_id)
    target_user = (await db.execute(stmt)).scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Generate token with special impersonation claim
    # Actually, we would modify `create_access_token` to accept claims,
    # but here we generate standard for demonstration.
    access_token = create_access_token(subject=target_user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "impersonator_id": current_user.id
    }
