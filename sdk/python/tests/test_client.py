import pytest
import respx
import httpx
from openrag.client import OpenRAGClient

@pytest.fixture
def client():
    return OpenRAGClient(api_key="test-key", tenant_id="test-tenant", base_url="https://api.test.com/v1")

@respx.mock
def test_get_collections(client):
    respx.get("https://api.test.com/v1/collections").mock(return_value=httpx.Response(200, json=[{"id": "1", "name": "Test"}]))
    
    collections = client.get_collections()
    assert len(collections) == 1
    assert collections[0]["name"] == "Test"

@respx.mock
def test_create_collection(client):
    respx.post("https://api.test.com/v1/collections").mock(return_value=httpx.Response(201, json={"id": "2", "name": "New"}))
    
    result = client.create_collection("New", "Desc")
    assert result["id"] == "2"

@respx.mock
def test_auth_headers_injected(client):
    route = respx.get("https://api.test.com/v1/collections").mock(return_value=httpx.Response(200, json=[]))
    client.get_collections()
    
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer test-key"
    assert request.headers["X-Tenant-ID"] == "test-tenant"
