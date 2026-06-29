from typing import Any
import pyotp
import qrcode
import io
import base64
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db_session
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, add_token_to_blacklist
)
from app.core.dependencies import get_current_user, get_redis
from app.schemas.auth import (
    LoginRequest, MFALoginRequest, Token, RefreshTokenRequest,
    MFASetupResponse, MFAVerifyRequest, UserProfileUpdate,
    PasswordResetRequest, PasswordResetConfirm
)
from app.models.user import User
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Login with email and password."""
    # Note: Rate limiting should be applied here via slowapi decorator in main router inclusion
    stmt = select(User).where(User.email == credentials.email)
    user = (await db.execute(stmt)).scalars().first()

    if not user or not user.hashed_password:
        # Prevent timing attacks by hashing anyway
        verify_password(credentials.password, "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # MFA Check
    if user.mfa_enabled:
        raise HTTPException(
            status_code=403, 
            detail="MFA required. Use /auth/login/mfa with your code."
        )

    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # We could log this in audit log here or rely on Middleware

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    request: Request,
    refresh_req: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
) -> Any:
    """Logout by blacklisting the current access and refresh tokens."""
    # Blacklist logic
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
        await add_token_to_blacklist(redis, access_token, expires_in=3600)
    await add_token_to_blacklist(redis, refresh_req.refresh_token, expires_in=86400 * 7)
    
    return {"message": "Successfully logged out"}


@router.post("/login/mfa", response_model=Token)
@limiter.limit("5/minute")
async def login_with_mfa(
    request: Request,
    credentials: MFALoginRequest,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Login for users with MFA enabled. Requires email, password, and TOTP code."""
    stmt = select(User).where(User.email == credentials.email)
    user = (await db.execute(stmt)).scalars().first()

    if not user or not user.hashed_password:
        verify_password(credentials.password, "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled for this account")

    # Verify TOTP code
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(credentials.mfa_code, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Generate TOTP secret and QR code URI."""
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name="Enterprise RAG")
    
    # Temporarily store secret until verified
    current_user.mfa_secret = secret
    await db.commit()

    return {"secret": secret, "provisioning_uri": provisioning_uri}

@router.post("/mfa/verify")
async def verify_mfa(
    req: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Verify TOTP code and enable MFA."""
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")
        
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    current_user.mfa_enabled = True
    await db.commit()
    
    return {"message": "MFA enabled successfully"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user profile."""
    return current_user

@router.patch("/me")
async def update_me(
    profile: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Update current user profile."""
    if profile.name:
        current_user.name = profile.name
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/password-reset")
async def request_password_reset(
    req: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Request a password reset link (simulated for now, would send email)."""
    stmt = select(User).where(User.email == req.email)
    user = (await db.execute(stmt)).scalars().first()
    
    if user:
        # In a real app, send email with a temporary signed JWT
        # reset_token = create_access_token(subject=user.id, expires_delta=timedelta(minutes=15))
        # send_email(user.email, reset_token)
        pass
        
    # Always return 200 to prevent user enumeration
    return {"message": "If that email exists, a reset link has been sent."}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    req: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Confirm password reset using the token."""
    # Dummy logic for now since email sending is simulated
    # subject = verify_jwt(req.token)
    # update user password...
    return {"message": "Password successfully reset."}

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    req: RefreshTokenRequest,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """Issue a new access token using a valid refresh token."""
    from app.core.security import is_token_blacklisted
    from jose import jwt, JWTError
    from app.core.config import settings
    
    if await is_token_blacklisted(redis, req.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token revoked")
        
    try:
        payload = jwt.decode(req.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or deleted")
        
    new_access = create_access_token(subject=user.id)
    new_refresh = create_refresh_token(subject=user.id)
    
    # Blacklist old refresh token to enable token rotation
    await add_token_to_blacklist(redis, req.refresh_token, expires_in=86400 * 7)
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }
