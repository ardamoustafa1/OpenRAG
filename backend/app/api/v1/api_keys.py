import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.dependencies import get_current_user, get_current_tenant
from app.core.security import create_api_key
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyUpdate, ApiKeyResponse
from app.models.user import User, ApiKey
from app.models.tenant import Tenant

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List API Keys."""
    stmt = select(ApiKey).where(ApiKey.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=ApiKeyCreateResponse)
async def create_new_api_key(
    key_in: ApiKeyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant)
) -> Any:
    """Produce a new API Key. The raw key is returned only once."""
    raw_key, key_hash, key_prefix = create_api_key()
    
    new_key = ApiKey(
        tenant_id=tenant.id,
        user_id=current_user.id,
        name=key_in.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=key_in.permissions,
        expires_at=key_in.expires_at
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    # Return a dict so we can inject the raw_key just this once
    response_data = new_key.to_dict()
    response_data["raw_key"] = f"{key_prefix}.{raw_key}"
    
    return response_data

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Revoke (delete) an API key."""
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    api_key_obj = (await db.execute(stmt)).scalars().first()
    
    if not api_key_obj:
        raise HTTPException(status_code=404, detail="Key not found")
        
    await db.delete(api_key_obj)
    await db.commit()
    return {"message": "Key revoked successfully"}
