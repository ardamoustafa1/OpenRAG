import uuid
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import (
    get_current_tenant,
    get_current_user,
    get_db_session,
)
from app.main import app
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_list_users(mock_db_session, mock_current_user, mock_current_tenant):
    mock_current_user.role = "tenant_admin"
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant

    try:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_current_user]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/users")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["email"] == mock_current_user.email
    finally:
        app.dependency_overrides.clear()


async def test_create_user(mock_db_session, mock_current_user, mock_current_tenant):
    mock_current_user.role = "tenant_admin"
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant

    try:
        # 1. Existing user -> 400
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_current_user
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        payload = {
            "email": "test@openrag.com",
            "name": "New User",
            "role": "user",
            "password": "password123",
        }
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_400 = await client.post("/api/v1/users", json=payload)
        assert res_400.status_code == 400
        assert "User already exists" in res_400.json()["detail"]

        # 2. New user -> 200
        mock_scalars.first.return_value = None
        from datetime import UTC, datetime

        def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(UTC)
            obj.is_active = True
            obj.mfa_enabled = False

        mock_db_session.refresh.side_effect = fake_refresh
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_200 = await client.post("/api/v1/users", json=payload)
        assert res_200.status_code == 200
        assert res_200.json()["email"] == "test@openrag.com"
        mock_db_session.add.assert_called()
    finally:
        app.dependency_overrides.clear()


async def test_impersonate_user(mock_db_session, mock_current_user):
    mock_super_admin = User(
        id=uuid.uuid4(),
        email="admin@openrag.com",
        name="Super Admin",
        role="super_admin",
        is_active=True,
        tenant_id=uuid.uuid4(),
    )
    app.dependency_overrides[get_current_user] = lambda: mock_super_admin
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    try:
        # 1. Target user not found -> 404
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_404 = await client.post(f"/api/v1/users/{uuid.uuid4()}/impersonate")
        assert res_404.status_code == 404

        # 2. Target user found -> 200
        mock_scalars.first.return_value = mock_current_user
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_200 = await client.post(f"/api/v1/users/{uuid.uuid4()}/impersonate")
        assert res_200.status_code == 200
        assert "access_token" in res_200.json()
        assert res_200.json()["impersonator_id"] == str(mock_super_admin.id)
    finally:
        app.dependency_overrides.clear()
