import asyncio
import json
import uuid
from typing import Any

import jwt
import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from jwt.exceptions import PyJWTError as JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db_session
from app.core.dependencies import get_current_tenant, get_current_user, get_redis
from app.core.rate_limit import limiter

# Use explicit class names to prevent ambiguity
from app.models.document import Document, DocumentCollection
from app.models.tenant import Tenant
from app.models.types import RedisClient
from app.models.user import User
from app.rag.vector_store import vector_store
from app.services.storage import storage_service
from app.workers.ingestion_tasks import process_document

logger = structlog.get_logger()

router = APIRouter(tags=["Documents"])

# --- Collections ---


@router.get("/collections")
async def list_collections(
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> Any:
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
    tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    col = DocumentCollection(
        tenant_id=tenant.id, name=payload.name, description=payload.description
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return col


@router.delete("/collections/{id}")
async def delete_collection(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict[str, str]:
    stmt = select(DocumentCollection).where(
        DocumentCollection.id == id, DocumentCollection.tenant_id == tenant.id
    )
    col = (await db.execute(stmt)).scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Delete Qdrant collection to prevent orphaned vectors (data leak prevention)
    try:
        await vector_store.delete_collection(str(tenant.id), str(id))
    except Exception as e:
        logger.warning(
            "Failed to delete Qdrant collection — manual cleanup may be required",
            error=str(e),
            collection_id=str(id),
        )

    await db.delete(col)
    await db.commit()
    return {"message": "Collection deleted"}


# --- Documents ---


@router.get("/collections/{collection_id}/documents")
async def list_documents(
    collection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> Any:
    stmt = select(Document).where(
        Document.collection_id == collection_id, Document.tenant_id == tenant.id
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/collections/{collection_id}/documents/upload")
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    collection_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Uploads a file, saves to MinIO, and queues the Celery ingestion task."""

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {file.content_type}"
        )

    # 1. Verify Collection
    stmt = select(DocumentCollection).where(
        DocumentCollection.id == collection_id,
        DocumentCollection.tenant_id == tenant.id,
    )
    col = (await db.execute(stmt)).scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Read with size limit
    file_bytes = b""
    while chunk := await file.read(1024 * 1024):
        file_bytes += chunk
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Maximum size is 100MB."
            )

    # 2. Create DB Record (status=processing)
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        tenant_id=tenant.id,
        collection_id=col.id,
        original_filename=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_bytes),
        storage_path="",  # Will be updated after upload
        status="processing",
        created_by=user.id,
    )
    db.add(doc)
    await db.commit()

    # 3. Upload to MinIO
    object_name = storage_service.get_object_path(
        str(tenant.id), str(col.id), str(doc_id), file.filename or "unknown"
    )
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
        file.content_type or "application/octet-stream",
    )

    return {
        "message": "Document uploaded and processing started",
        "document_id": doc_id,
    }


@router.delete("/collections/{collection_id}/documents/{document_id}")
async def delete_document(
    collection_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict[str, str]:
    stmt = select(Document).where(
        Document.id == document_id, Document.tenant_id == tenant.id
    )
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from Qdrant
    await vector_store.delete_by_document(
        str(tenant.id), str(collection_id), str(document_id)
    )

    # Delete from DB
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}


@router.post("/collections/{collection_id}/documents/{document_id}/retry")
async def retry_document(
    collection_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict[str, str]:
    stmt = select(Document).where(
        Document.id == document_id, Document.tenant_id == tenant.id
    )
    doc = (await db.execute(stmt)).scalars().first()
    if not doc or doc.status != "failed":
        raise HTTPException(
            status_code=400, detail="Document not found or not in failed state"
        )

    doc.status = "processing"
    await db.commit()

    object_name = storage_service.get_object_path(
        str(tenant.id), str(collection_id), str(document_id), doc.original_filename
    )

    process_document.delay(
        str(document_id),
        str(tenant.id),
        str(collection_id),
        object_name,
        doc.original_filename,
        doc.mime_type,
    )
    return {"message": "Retry queued"}


# --- WebSockets ---


@router.websocket("/ws/documents/{document_id}/progress")
async def document_progress_ws(
    websocket: WebSocket, document_id: str, redis: RedisClient = Depends(get_redis)
) -> None:
    """
    Real-time document processing progress via Redis Pub/Sub.
    """
    # Retrieve token from subprotocols
    subprotocols = websocket.headers.get("Sec-WebSocket-Protocol", "").split(",")
    token = None
    for protocol in subprotocols:
        protocol = protocol.strip()
        if protocol.startswith("Bearer-"):
            token = protocol.replace("Bearer-", "")
            break

    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub claim")
    except (JWTError, ValueError):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    pubsub = redis.pubsub()
    channel = f"doc_progress:{document_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            # We use a slight timeout to keep checking for client disconnects
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
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
