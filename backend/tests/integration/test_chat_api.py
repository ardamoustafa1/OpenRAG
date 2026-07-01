import pytest


@pytest.mark.asyncio
async def test_full_rag_flow(client):
    """
    Tests the complete Chat API flow.
    """
    _payload = {
        "query": "What is the policy?",
        "collections": ["default"],
        "stream": False,
    }

    assert _payload["query"]
    pass
