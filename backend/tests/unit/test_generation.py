import json
from unittest.mock import patch

import pytest

from app.rag.generation import GenerationService


@pytest.mark.asyncio
async def test_stream_chat():
    service = GenerationService()

    # Mock the LLM client async generator
    async def mock_generator():
        yield "Hello"
        yield " World"

    with patch("app.rag.generation.llm_client.astream_chat") as mock_stream:
        mock_stream.return_value = mock_generator()

        messages = [{"role": "user", "content": "Hi"}]
        context = "Some context"
        settings = {"system_prompt": "Custom prompt"}
        sources = [{"id": "doc1", "title": "Doc 1"}]

        gen = service.stream_chat(
            model="test-model",
            messages=messages,
            context_string=context,
            tenant_settings=settings,
            tenant_id="tenant1",
            sources=sources,
        )

        chunks = [chunk async for chunk in gen]

        # Verify chunk structure
        assert len(chunks) == 4
        assert chunks[0].startswith("data: ")
        assert json.loads(chunks[0][6:].strip())["content"] == "Hello"

        assert chunks[1].startswith("data: ")
        assert json.loads(chunks[1][6:].strip())["content"] == " World"

        # Sources chunk
        sources_payload = json.loads(chunks[2][6:].strip())
        assert sources_payload["type"] == "sources"
        assert sources_payload["sources"] == sources

        # Done chunk
        assert chunks[3] == "data: [DONE]\n\n"
