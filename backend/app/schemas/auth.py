from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MFALoginRequest(BaseModel):
    """Used when a user has MFA enabled — sends email, password AND TOTP code."""

    email: EmailStr
    password: str
    mfa_code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MFAVerifyRequest(BaseModel):
    code: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class UserProfileUpdate(BaseModel):
    name: str | None = None
    # Cannot update role or email through standard profile update

    model_config = ConfigDict(from_attributes=True)
