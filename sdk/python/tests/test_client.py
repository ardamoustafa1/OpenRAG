import pytest
import respx
import httpx
from ai_platform.client import AIPlatformClient, RateLimitError

@pytest.fixture
def client():
    return AIPlatformClient(api_key="test-key", tenant_url="http://api.test")

@respx.mock
def test_chat_success(client):
    respx.post("http://api.test/api/v1/chat").mock(return_value=httpx.Response(200, json={"message": "success"}))
    response = client.chat("hello", ["col1"])
    assert response["message"] == "success"

@respx.mock
def test_chat_rate_limit_retry(client):
    route = respx.post("http://api.test/api/v1/chat")
    route.side_effect = [
        httpx.Response(429, text="Rate Limited"),
        httpx.Response(200, json={"message": "success after retry"})
    ]
    
    response = client.chat("hello", ["col1"])
    assert response["message"] == "success after retry"
    assert route.call_count == 2

@respx.mock
@pytest.mark.asyncio
async def test_achat_success():
    client = AIPlatformClient(api_key="test-key", tenant_url="http://api.test")
    respx.post("http://api.test/api/v1/chat").mock(return_value=httpx.Response(200, json={"message": "async success"}))
    response = await client.achat("hello", ["col1"])
    assert response["message"] == "async success"
    await client.aclose()
