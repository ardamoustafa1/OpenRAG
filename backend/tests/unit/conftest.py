import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.user import User
from app.models.tenant import Tenant
import uuid

@pytest.fixture
def mock_db_session():
    """Provides a mocked AsyncSession for database operations without a real DB."""
    session = AsyncMock()
    # Support basic queries like session.execute(stmt).scalars().first()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result
    return session

@pytest.fixture
def mock_redis():
    """Provides a mocked Redis instance."""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest.fixture
def mock_current_user():
    """Provides a default user object."""
    return User(
        id=uuid.uuid4(),
        email="test@openrag.com",
        name="Test User",
        role="user",
        is_active=True,
        tenant_id=uuid.uuid4()
    )

@pytest.fixture
def mock_current_tenant():
    """Provides a default tenant object."""
    return Tenant(
        id=uuid.uuid4(),
        name="Test Tenant",
        subdomain="test",
        settings={}
    )
