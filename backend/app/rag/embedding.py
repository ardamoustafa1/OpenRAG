import numpy as np
import structlog

from app.llm.client import llm_client

logger = structlog.get_logger()


class EmbeddingService:
    """
    Handles batched embedding generation using the LLM orchestration layer.
    """

    def __init__(self, model_name: str = "bge-m3", batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size

    async def embed_chunks(self, chunks: list[dict], tenant_id: str) -> list[dict]:
        """
        Takes a list of chunk dictionaries, generates embeddings in batches,
        normalizes them for cosine similarity, and adds the embedding vector to the dict.
        """
        logger.info(
            "Starting embedding generation",
            total_chunks=len(chunks),
            model=self.model_name,
        )

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            texts = [chunk["text"] for chunk in batch]

            try:
                # Call LiteLLM proxy
                embeddings = await llm_client.aembed_batch(
                    model=self.model_name, input_texts=texts, tenant_id=tenant_id
                )

                # Normalize and assign
                for j, emb in enumerate(embeddings):
                    # L2 Normalize the vector for faster Cosine similarity in Qdrant
                    vec = np.array(emb, dtype=np.float32)
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm

                    batch[j]["embedding"] = vec.tolist()

            except Exception as e:
                logger.error("Failed to embed batch", batch_index=i, error=str(e))
                raise

        logger.info("Embedding generation completed")
        return chunks


embedding_service = EmbeddingService()
