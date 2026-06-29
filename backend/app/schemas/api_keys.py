from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ApiKeyBase(BaseModel):
    name: str
    permissions: list[Any] = []
    expires_at: datetime | None = None

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyCreateResponse(ApiKeyBase):
    id: UUID
    key_prefix: str
    raw_key: str  # ONLY RETURNED ONCE
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApiKeyUpdate(BaseModel):
    name: str | None = None
    permissions: list[Any] | None = None
    is_active: bool | None = None

class ApiKeyResponse(ApiKeyBase):
    id: UUID
    key_prefix: str
    user_id: UUID | None
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
