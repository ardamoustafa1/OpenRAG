import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.chat import Conversation
from app.models.document import DocumentCollection
from app.models.tenant import Tenant
from app.models.user import User


@pytest_asyncio.fixture
async def setup_tenants_and_users(db_session: AsyncSession):
    # Create Tenant A
    tenant_a = Tenant(id=uuid.uuid4(), name="Tenant A", slug="tenant-a")
    # Create Tenant B
    tenant_b = Tenant(id=uuid.uuid4(), name="Tenant B", slug="tenant-b")

    db_session.add_all([tenant_a, tenant_b])
    await db_session.commit()

    # Create User A
    user_a = User(
        id=uuid.uuid4(), tenant_id=tenant_a.id, email="user_a@test.com", name="User A"
    )
    # Create User B
    user_b = User(
        id=uuid.uuid4(), tenant_id=tenant_b.id, email="user_b@test.com", name="User B"
    )

    db_session.add_all([user_a, user_b])
    await db_session.commit()

    # Create Collection for Tenant A
    col_a = DocumentCollection(
        id=uuid.uuid4(), tenant_id=tenant_a.id, name="Tenant A Docs"
    )
    db_session.add(col_a)

    # Create Conversation for Tenant A
    conv_a = Conversation(
        id=uuid.uuid4(), tenant_id=tenant_a.id, user_id=user_a.id, title="Tenant A Chat"
    )
    db_session.add(conv_a)

    await db_session.commit()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "user_a": user_a,
        "user_b": user_b,
        "collection_a": col_a,
        "conversation_a": conv_a,
    }


@pytest.fixture
def auth_headers_tenant_a(setup_tenants_and_users):
    token = create_access_token(str(setup_tenants_and_users["user_a"].id))
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(setup_tenants_and_users["tenant_a"].id),
    }


@pytest.fixture
def auth_headers_tenant_b(setup_tenants_and_users):
    token = create_access_token(str(setup_tenants_and_users["user_b"].id))
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(setup_tenants_and_users["tenant_b"].id),
    }


@pytest.fixture
def auth_headers_tenant_b_spoofed(setup_tenants_and_users):
    # User B trying to act as Tenant A by spoofing X-Tenant-ID header
    token = create_access_token(str(setup_tenants_and_users["user_b"].id))
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(setup_tenants_and_users["tenant_a"].id),
    }


@pytest.mark.asyncio
async def test_tenant_isolation_collections(
    client: AsyncClient, setup_tenants_and_users, auth_headers_tenant_b
):
    """Ensures Tenant B cannot access Tenant A's collections."""
    col_a = setup_tenants_and_users["collection_a"]

    # Tenant B tries to fetch Tenant A's collection documents
    response = await client.get(
        f"/api/v1/collections/{col_a.id}/documents", headers=auth_headers_tenant_b
    )

    # Should not exist in their context
    assert (
        response.status_code == 200
    )  # It returns [] because the route scopes by tenant_id
    assert response.json() == []


@pytest.mark.asyncio
async def test_tenant_isolation_conversations(
    client: AsyncClient, setup_tenants_and_users, auth_headers_tenant_b
):
    """Ensures Tenant B cannot fetch Tenant A's chat conversation."""
    conv_a = setup_tenants_and_users["conversation_a"]

    # We try to send a message to Tenant A's conversation using Tenant B's token
    payload = {
        "content": "Hello",
        "collection_id": str(setup_tenants_and_users["collection_a"].id),
    }
    response = await client.post(
        f"/api/v1/conversations/{conv_a.id}/messages",
        json=payload,
        headers=auth_headers_tenant_b,
    )

    # Must be completely hidden (404)
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


@pytest.mark.asyncio
async def test_tenant_spoofing_prevented(
    client: AsyncClient, setup_tenants_and_users, auth_headers_tenant_b_spoofed
):
    """Ensures User B cannot spoof X-Tenant-ID to access Tenant A."""
    response = await client.get(
        "/api/v1/collections", headers=auth_headers_tenant_b_spoofed
    )

    # The TenantMiddleware should block this because User B does not belong to Tenant A
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not belong to requested tenant"
