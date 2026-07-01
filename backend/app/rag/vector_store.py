import uuid

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

logger = structlog.get_logger()


class VectorStoreService:
    """
    Qdrant integration for tenant-isolated vector storage.
    """

    def __init__(self):
        self.client = AsyncQdrantClient(
            url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
            check_compatibility=False,
            # If QDRANT_API_KEY is an empty string or None, don't pass it or pass None
        )

    def _collection_name(self, tenant_id: str, collection_id: str) -> str:
        # e.g. tenant_123e4567_col_890e1234
        return f"tenant_{str(tenant_id).replace('-','')}_col_{str(collection_id).replace('-','')}"

    async def ensure_collection(
        self, tenant_id: str, collection_id: str, vector_size: int = 1024
    ):
        """Creates the collection if it doesn't exist."""
        col_name = self._collection_name(tenant_id, collection_id)
        try:
            exists = await self.client.collection_exists(col_name)
            if not exists:
                await self.client.create_collection(
                    collection_name=col_name,
                    vectors_config=VectorParams(
                        size=vector_size, distance=Distance.COSINE
                    ),
                )
                # Create payload index for fast document_id filtering
                await self.client.create_payload_index(
                    collection_name=col_name,
                    field_name="document_id",
                    field_schema="keyword",
                )
                logger.info("Created Qdrant collection", collection_name=col_name)
        except Exception as e:
            logger.error("Failed to ensure Qdrant collection", error=str(e))
            raise

    async def upsert_chunks(
        self, tenant_id: str, collection_id: str, chunks: list[dict]
    ):
        """Uploads a batch of chunks to the specific tenant collection."""
        if not chunks:
            return

        col_name = self._collection_name(tenant_id, collection_id)

        # We need to know the vector size from the first chunk to ensure collection
        vector_size = len(chunks[0]["embedding"])
        await self.ensure_collection(tenant_id, collection_id, vector_size)

        points = []
        for chunk in chunks:
            # Generate a deterministic UUID for the chunk based on document_id + text hash
            # or just use random if we delete first. We'll use random for simplicity.
            point_id = str(uuid.uuid4())

            payload = {k: v for k, v in chunk.items() if k != "embedding"}

            points.append(
                PointStruct(id=point_id, vector=chunk["embedding"], payload=payload)
            )

        try:
            await self.client.upsert(collection_name=col_name, points=points)
            logger.info(
                "Upserted chunks to Qdrant", count=len(points), collection_name=col_name
            )
        except Exception as e:
            logger.error("Failed to upsert points to Qdrant", error=str(e))
            raise

    async def delete_by_document(
        self, tenant_id: str, collection_id: str, document_id: str
    ):
        """Deletes all chunks belonging to a specific document."""
        col_name = self._collection_name(tenant_id, collection_id)
        try:
            if await self.client.collection_exists(col_name):
                # We use the payload index to delete
                from qdrant_client.http import models

                await self.client.delete(
                    collection_name=col_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="document_id",
                                    match=models.MatchValue(value=str(document_id)),
                                )
                            ]
                        )
                    ),
                )
                logger.info(
                    "Deleted document chunks from Qdrant", document_id=document_id
                )
        except Exception as e:
            logger.error("Failed to delete document from Qdrant", error=str(e))
            raise


vector_store = VectorStoreService()
