import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.db import get_db_session
from app.core.config import settings
from app.core.dependencies import get_current_tenant, get_current_user, get_redis
from app.models.tenant import Tenant
from app.models.user import User
# Use explicit class names to prevent ambiguity
from app.models.document import DocumentCollection, Document
from app.services.storage import storage_service
from app.workers.ingestion_tasks import process_document
from app.rag.vector_store import vector_store
import structlog

logger = structlog.get_logger()

router = APIRouter(tags=["Documents"])

# --- Collections ---

@router.get("/collections")
async def list_collections(
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    stmt = select(DocumentCollection).where(DocumentCollection.tenant_id == tenant.id)
    result = await db.execute(stmt)
    return result.scalars().all()

class CreateCollectionRequest(BaseModel):
    name: str
    description: str | None = None

@router.post("/collections")
async def create_collection(
    payload: CreateCollectionRequest,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    col = DocumentCollection(tenant_id=tenant.id, name=payload.name, description=payload.description)
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return col

@router.delete("/collections/{id}")
async def delete_collection(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    stmt = select(DocumentCollection).where(DocumentCollection.id == id, DocumentCollection.tenant_id == tenant.id)
    col = (await db.execute(stmt)).scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    # Also delete Qdrant collection
    # Note: In real app, do this async or handle errors safely
    # await vector_store.delete_collection(str(tenant.id), str(id))
    
    await db.delete(col)
    await db.commit()
    return {"message": "Collection deleted"}

# --- Documents ---

@router.get("/collections/{collection_id}/documents")
async def list_documents(
    collection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    stmt = select(Document).where(Document.collection_id == collection_id, Document.tenant_id == tenant.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/collections/{collection_id}/documents/upload")
async def upload_document(
    collection_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user)
):
    """Uploads a file, saves to MinIO, and queues the Celery ingestion task."""
    
    # 1. Verify Collection
    stmt = select(DocumentCollection).where(DocumentCollection.id == collection_id, DocumentCollection.tenant_id == tenant.id)
    col = (await db.execute(stmt)).scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    # 2. Create DB Record (status=processing)
    doc_id = uuid.uuid4()
    file_bytes = await file.read()
    doc = Document(
        id=doc_id,
        tenant_id=tenant.id,
        collection_id=col.id,
        original_filename=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_bytes),
        storage_path="",  # Will be updated after upload
        status="processing",
        created_by=user.id
    )
    db.add(doc)
    await db.commit()
    
    # 3. Upload to MinIO
    object_name = storage_service.get_object_path(str(tenant.id), str(col.id), str(doc_id), file.filename or "unknown")
    storage_service.upload_file(object_name, file_bytes, file.content_type)
    
    # 4. Update storage_path in DB
    doc.storage_path = object_name
    await db.commit()
    
    # 5. Enqueue Celery Task
    process_document.delay(
        str(doc_id),
        str(tenant.id),
        str(col.id),
        object_name,
        file.filename or "unknown",
        file.content_type or "application/octet-stream"
    )
    
    return {"message": "Document uploaded and processing started", "document_id": doc_id}

@router.delete("/collections/{collection_id}/documents/{document_id}")
async def delete_document(
    collection_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant.id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from Qdrant
    await vector_store.delete_by_document(str(tenant.id), str(collection_id), str(document_id))
    
    # Delete from DB
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}

@router.post("/collections/{collection_id}/documents/{document_id}/retry")
async def retry_document(
    collection_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant)
):
    stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant.id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc or doc.status != "failed":
        raise HTTPException(status_code=400, detail="Document not found or not in failed state")

    doc.status = "processing"
    await db.commit()
    
    object_name = storage_service.get_object_path(str(tenant.id), str(collection_id), str(document_id), doc.original_filename)
    
    process_document.delay(
        str(document_id),
        str(tenant.id),
        str(collection_id),
        object_name,
        doc.original_filename,
        doc.mime_type
    )
    return {"message": "Retry queued"}

# --- WebSockets ---

@router.websocket("/ws/documents/{document_id}/progress")
async def document_progress_ws(websocket: WebSocket, document_id: str, redis: Redis = Depends(get_redis)):
    """
    Real-time document processing progress via Redis Pub/Sub.
    """
    await websocket.accept()
    pubsub = redis.pubsub()
    channel = f"doc_progress:{document_id}"
    await pubsub.subscribe(channel)
    
    try:
        while True:
            # We use a slight timeout to keep checking for client disconnects
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = message["data"].decode("utf-8")
                await websocket.send_text(data)
                
                # Close connection if completed or failed
                payload = json.loads(data)
                if payload.get("stage") in ["completed", "failed"]:
                    break
                    
            # Check if client disconnected by attempting to receive
            # This is a bit tricky in WebSockets; typically ping/pong is better
            # For simplicity, we just loop until done.
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await websocket.close()
