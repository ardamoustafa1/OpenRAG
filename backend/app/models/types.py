import os
from sqlalchemy import TypeDecorator, String
from cryptography.fernet import Fernet
from app.core.config import settings
import structlog
import base64
import hashlib

logger = structlog.get_logger()

# We derive a 32-url-safe-base64 key from settings.SECRET_KEY for Fernet
# If SECRET_KEY is changed, old data will be unreadable unless key rotation is implemented.
_fernet_key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
_fernet = Fernet(_fernet_key)

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that seamlessly encrypts data on write and
    decrypts it on read using Fernet symmetric encryption.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        try:
            return _fernet.encrypt(value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error("Failed to encrypt value", error=str(e))
            raise ValueError("Encryption failed") from e

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return _fernet.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error("Failed to decrypt value", error=str(e))
            # Return raw value as fallback if it was already plaintext before encryption was enabled,
            # though in strict environments you should raise an error.
            return value
