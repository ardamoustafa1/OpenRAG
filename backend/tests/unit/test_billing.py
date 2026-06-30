import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import get_current_user, get_db_session, get_current_tenant
from app.core.config import settings

pytestmark = pytest.mark.asyncio

async def test_billing_unconfigured(mock_db_session, mock_current_user, mock_current_tenant):
    # Temporarily remove stripe API key
    original_key = settings.STRIPE_API_KEY
    settings.STRIPE_API_KEY = None
    
    mock_current_user.role = "tenant_admin"
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/billing/portal")
        
    assert response.status_code == 503
    assert "Billing service is not configured" in response.json()["detail"]
    
    # Restore
    settings.STRIPE_API_KEY = original_key
    app.dependency_overrides.clear()
