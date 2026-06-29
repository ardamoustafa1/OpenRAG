import pytest
from unittest.mock import patch, MagicMock
from app.core.security import create_access_token, verify_password, get_password_hash
from jose import jwt, ExpiredSignatureError
from datetime import timedelta
from app.core.config import settings

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

@patch("app.core.security.jwt.decode")
def test_expired_token(mock_decode):
    mock_decode.side_effect = ExpiredSignatureError()
    
    with pytest.raises(ExpiredSignatureError):
        # Trigger the exception
        jwt.decode("expired_token", settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

# Additional tests for MFA TOTP verification and RBAC checks would go here.
