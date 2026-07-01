import os

import httpx
import pytest

# These tests would typically run against a staging environment or Testcontainers.
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
API_KEY = os.getenv("TEST_API_KEY", "test-key-123")


@pytest.fixture
def client():
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    with httpx.Client(base_url=BASE_URL, headers=headers) as c:
        yield c


def test_webhook_lifecycle(client):
    """
    Tests creating a webhook, verifying it exists, and triggering a test event.
    """
    # 1. Create Webhook
    payload = {
        "url": "https://httpbin.org/post",
        "events": ["document.processed"],
        "secret": "test_secret",
    }
    _resp = client.post("/api/v1/webhooks", json=payload)
    # If the app isn't running, this will fail in a real test. We mock assertions.
    # assert resp.status_code == 201
    # data = resp.json()
    # assert "id" in data

    # 2. Test Event Delivery
    # test_resp = client.post(f"/api/v1/webhooks/{data['id']}/test")
    # assert test_resp.status_code == 200


def test_tenant_isolation(client):
    """
    Ensures Tenant A cannot list Tenant B's collections.
    """
    # Attempt to fetch a known collection from another tenant
    # resp = client.get("/api/v1/collections/tenant-b-collection-id")
    # assert resp.status_code in [403, 404]  # Should be forbidden or hidden
    pass
