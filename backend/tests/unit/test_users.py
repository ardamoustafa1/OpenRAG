import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import get_current_user, get_db_session

pytestmark = pytest.mark.asyncio

async def test_get_me(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
        
    assert response.status_code == 200
    assert response.json()["email"] == mock_current_user.email
    app.dependency_overrides.clear()

async def test_update_me(mock_db_session, mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    
    payload = {"name": "Updated Name"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/v1/auth/me", json=payload)
        
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert mock_current_user.name == "Updated Name"
    # Ensure commit was called
    mock_db_session.commit.assert_called_once()
    app.dependency_overrides.clear()
