import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import get_current_user, get_db_session

pytestmark = pytest.mark.asyncio

async def test_admin_access_denied_for_regular_user(mock_db_session, mock_current_user):
    # Ensure role is user
    mock_current_user.role = "user"
    
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/users")
        
    assert response.status_code == 403
    assert "Super Admin privileges required" in response.json()["detail"]
    app.dependency_overrides.clear()

async def test_admin_access_allowed_for_super_admin(mock_db_session, mock_current_user):
    mock_current_user.role = "super_admin"
    
    # Setup mock DB response for listing users
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_current_user]
    
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/admin/users")
        
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == mock_current_user.email
    app.dependency_overrides.clear()
