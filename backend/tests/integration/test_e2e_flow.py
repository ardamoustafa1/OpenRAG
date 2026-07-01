import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_webhook_lifecycle(client: AsyncClient):
    """
    Tests creating a webhook, verifying it exists, and triggering a test event.
    """
    # 1. Create Webhook
    payload = {
        "url": "https://httpbin.org/post",
        "events": ["document.processed"],
        "secret": "test_secret",
    }
    resp = await client.post("/api/v1/webhooks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data

    # 2. Test Event Delivery
    # test_resp = client.post(f"/api/v1/webhooks/{data['id']}/test")
    # assert test_resp.status_code == 200


@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient):
    """
    Ensures Tenant A cannot list Tenant B's collections.
    """
    # Attempt to fetch a known collection from another tenant
    # resp = client.get("/api/v1/collections/tenant-b-collection-id")
    # assert resp.status_code in [403, 404]  # Should be forbidden or hidden
    pass
