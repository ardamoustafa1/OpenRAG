import pytest
import numpy as np
from unittest.mock import patch, AsyncMock
from app.rag.embedding import EmbeddingService

@pytest.mark.asyncio
async def test_embed_chunks():
    service = EmbeddingService(batch_size=2)
    chunks = [
        {"text": "Hello world"},
        {"text": "Test chunk two"}
    ]
    
    mock_embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6]
    ]
    
    with patch("app.rag.embedding.llm_client.aembed_batch", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embeddings
        
        result = await service.embed_chunks(chunks, tenant_id="test-tenant")
        
        mock_embed.assert_called_once_with(
            model="bge-m3",
            input_texts=["Hello world", "Test chunk two"],
            tenant_id="test-tenant"
        )
        
        assert len(result) == 2
        assert "embedding" in result[0]
        assert "embedding" in result[1]
        
        # Check normalization
        vec1 = np.array(result[0]["embedding"])
        assert np.isclose(np.linalg.norm(vec1), 1.0)
