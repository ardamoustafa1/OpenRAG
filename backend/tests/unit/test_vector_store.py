import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag.vector_store import VectorStore

pytestmark = pytest.mark.asyncio

async def test_vector_store_upsert():
    with patch("app.rag.vector_store.qdrant_client") as mock_qdrant:
        mock_qdrant.upsert = AsyncMock()
        
        vs = VectorStore()
        chunks = [
            {"id": "uuid1", "embedding": [0.1, 0.2], "payload": {"text": "hello"}},
            {"id": "uuid2", "embedding": [0.3, 0.4], "payload": {"text": "world"}}
        ]
        
        await vs.upsert_chunks("tenant1", "collection1", chunks)
        
        # Verify qdrant upsert was called
        mock_qdrant.upsert.assert_called_once()

async def test_vector_store_search():
    with patch("app.rag.vector_store.qdrant_client") as mock_qdrant:
        mock_result = MagicMock()
        mock_result.id = "uuid1"
        mock_result.score = 0.95
        mock_result.payload = {"text": "hello"}
        mock_qdrant.search = AsyncMock(return_value=[mock_result])
        
        vs = VectorStore()
        results = await vs.search("tenant1", "collection1", [0.1, 0.2], limit=1)
        
        assert len(results) == 1
        assert results[0]["id"] == "uuid1"
        assert results[0]["score"] == 0.95
