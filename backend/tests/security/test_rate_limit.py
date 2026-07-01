import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rate_limiting_enforcement(client: AsyncClient):
    """
    Test that the rate limiter is working correctly and blocks requests
    when the threshold is exceeded.
    Assuming the /api/v1/auth/login endpoint has a low rate limit (e.g., 5/minute).
    """
    url = "/api/v1/auth/login"
    payload = {"username": "testuser", "password": "wrongpassword"}

    # We will simulate 10 requests. Depending on the actual rate limit configured,
    # the exact number might vary, but an enterprise platform login should block after a few attempts.
    # In this generic test, we expect at least one 429 status code if rate limiting is enabled.
    responses = []
    for _ in range(15):
        res = await client.post(url, data=payload)
        responses.append(res.status_code)

        if res.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            break

    assert (
        status.HTTP_429_TOO_MANY_REQUESTS in responses
    ), "Rate limiting did not trigger a 429 response."
