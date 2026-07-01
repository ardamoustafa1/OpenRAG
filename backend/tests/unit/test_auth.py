from datetime import UTC, datetime, timedelta

import jwt
import pytest
from jwt.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_create_access_token():
    data = {"sub": "user-123", "role": "tenant_admin"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "tenant_admin"
    assert "exp" in decoded


def test_expired_token():
    token = jwt.encode(
        {
            "sub": "user-123",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# Additional tests for MFA TOTP verification and RBAC checks would go here.
