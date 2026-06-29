from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str

class UserCreate(UserBase):
    password: str | None = None  # Null for SSO/Invite

class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None

class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    mfa_enabled: bool
    sso_provider: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
