import asyncio
import json
import structlog
from redis.asyncio import Redis

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.db import async_session_factory
from app.models.document import Document
from app.services.storage import storage_service
from app.rag.extraction import extraction_service
from app.rag.chunking import chunking_service
from app.rag.embedding import embedding_service
from app.rag.vector_store import vector_store
from rank_bm25 import BM25Okapi
import pickle
from sqlalchemy import select
from app.models.document import DocumentChunk

logger = structlog.get_logger()

async def emit_progress(redis: Redis, document_id: str, stage: str, progress: float, message: str):
    """Publish progress to a Redis channel specific to the document."""
    channel = f"doc_progress:{document_id}"
    payload = {
        "document_id": document_id,
        "stage": stage,
        "progress": progress,
        "message": message
    }
    await redis.publish(channel, json.dumps(payload))
    logger.info("Progress updated", document_id=document_id, stage=stage, progress=progress)

async def _process_document_async(document_id: str, tenant_id: str, collection_id: str, object_name: str, filename: str, content_type: str):
    redis = Redis.from_url(settings.REDIS_URL)
    
    async with async_session_factory() as db:
        try:
            await emit_progress(redis, document_id, "extraction", 0.1, "Downloading document...")
            
            # Step 1: Download from MinIO
            file_bytes = storage_service.download_file(object_name)
            
            # Step 2 & 3 & 4: Extract and clean
            await emit_progress(redis, document_id, "extraction", 0.3, "Extracting text and metadata...")
            extraction_result = extraction_service.process_file(file_bytes, filename, content_type)
            elements = extraction_result["elements"]
            
            # Step 5: Semantic Chunking
            await emit_progress(redis, document_id, "chunking", 0.5, "Chunking document structurally...")
            chunks = chunking_service.chunk_elements(elements, document_id=document_id)
            total_tokens = sum(c["token_count"] for c in chunks)
            
            # Step 6: Embedding
            await emit_progress(redis, document_id, "embedding", 0.7, "Generating vector embeddings...")
            embedded_chunks = await embedding_service.embed_chunks(chunks, tenant_id=tenant_id)
            
            # Step 7: Qdrant Upsert
            await emit_progress(redis, document_id, "indexing", 0.9, "Indexing vectors to Qdrant...")
            await vector_store.upsert_chunks(tenant_id, collection_id, embedded_chunks)
            
            # Step 8: Update PostgreSQL Status
            doc = await db.get(Document, document_id)
            if doc:
                doc.status = "ready"
                doc.token_count = total_tokens
                doc.chunk_count = len(chunks)
                await db.commit()
                
            await emit_progress(redis, document_id, "completed", 1.0, "Document processed successfully.")
            logger.info("Document processing completed successfully", document_id=document_id)
            
            # Step 9: Trigger BM25 index rebuild for the collection
            build_bm25_index.delay(tenant_id, collection_id)
            
        except Exception as e:
            logger.error("Document processing failed", document_id=document_id, error=str(e))
            # Update DB with error
            doc = await db.get(Document, document_id)
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                await db.commit()
                
            await emit_progress(redis, document_id, "failed", 0.0, f"Error: {str(e)}")
            raise e
        finally:
            await redis.close()


@celery_app.task(bind=True, max_retries=3, retry_backoff=True)
def process_document(self, document_id: str, tenant_id: str, collection_id: str, object_name: str, filename: str, content_type: str):
    """
    Synchronous Celery task wrapper that runs the async pipeline.
    """
    logger.info("Celery task started: process_document", document_id=document_id)
    try:
        asyncio.run(_process_document_async(
            document_id=document_id,
            tenant_id=tenant_id,
            collection_id=collection_id,
            object_name=object_name,
            filename=filename,
            content_type=content_type
        ))
    except Exception as exc:
        logger.error("Task failed, scheduling retry", document_id=document_id, error=str(exc))
        raise self.retry(exc=exc)

async def _build_bm25_index_async(tenant_id: str, collection_id: str):
    """Fetches all chunks for a collection, builds BM25, and caches in Redis."""
    redis = Redis.from_url(settings.REDIS_URL)
    
    async with async_session_factory() as db:
        try:
            # Fetch all chunks for this collection via a join
            stmt = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.collection_id == collection_id)
            )
            result = await db.execute(stmt)
            chunks = result.scalars().all()
            
            if not chunks:
                return
            
            # Tokenize content
            corpus = [chunk.content.lower().split() for chunk in chunks]
            
            # Build BM25
            bm25 = BM25Okapi(corpus)
            
            # Create mapping for retrieval
            mapping = [{"id": str(chunk.qdrant_point_id), "payload": chunk.metadata_} for chunk in chunks]
            
            # Cache payload
            cache_payload = {
                "model": bm25,
                "mapping": mapping
            }
            
            col_name = f"tenant_{str(tenant_id).replace('-','')}_col_{str(collection_id).replace('-','')}"
            await redis.set(f"bm25:{col_name}", pickle.dumps(cache_payload))
            logger.info("BM25 index built and cached successfully", collection_id=collection_id, chunks=len(chunks))
            
        except Exception as e:
            logger.error("BM25 index build failed", error=str(e), collection_id=collection_id)
        finally:
            await redis.close()

@celery_app.task(bind=True)
def build_bm25_index(self, tenant_id: str, collection_id: str):
    """Synchronous Celery task wrapper to build BM25 index."""
    logger.info("Celery task started: build_bm25_index", collection_id=collection_id)
    try:
        asyncio.run(_build_bm25_index_async(tenant_id, collection_id))
    except Exception as exc:
        logger.error("BM25 build task failed", error=str(exc))
        raise self.retry(exc=exc)
