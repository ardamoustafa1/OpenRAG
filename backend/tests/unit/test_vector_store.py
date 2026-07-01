from unittest.mock import AsyncMock, patch

import pytest

from app.rag.vector_store import VectorStoreService

pytestmark = pytest.mark.asyncio


async def test_vector_store_upsert():
    with patch("app.rag.vector_store.AsyncQdrantClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.collection_exists = AsyncMock(return_value=True)
        mock_client.upsert = AsyncMock()

        vs = VectorStoreService()
        chunks = [
            {"id": "uuid1", "embedding": [0.1, 0.2], "payload": {"text": "hello"}},
            {"id": "uuid2", "embedding": [0.3, 0.4], "payload": {"text": "world"}},
        ]

        await vs.upsert_chunks("tenant1", "collection1", chunks)

        mock_client.collection_exists.assert_awaited_once()
        mock_client.upsert.assert_awaited_once()


async def test_vector_store_creates_missing_collection():
    with patch("app.rag.vector_store.AsyncQdrantClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.collection_exists = AsyncMock(return_value=False)
        mock_client.create_collection = AsyncMock()
        mock_client.create_payload_index = AsyncMock()

        vs = VectorStoreService()
        await vs.ensure_collection("tenant1", "collection1", vector_size=2)

        mock_client.create_collection.assert_awaited_once()
        mock_client.create_payload_index.assert_awaited_once()
