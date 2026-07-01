import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.document import Document, DocumentCollection
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture
async def setup_document_test(db_session: AsyncSession):
    tenant = Tenant(id=uuid.uuid4(), name="Doc Tenant", slug="doc-tenant")
    user = User(
        id=uuid.uuid4(), tenant_id=tenant.id, email="doc@test.com", name="Doc User"
    )
    db_session.add_all([tenant, user])
    await db_session.commit()

    col = DocumentCollection(id=uuid.uuid4(), tenant_id=tenant.id, name="Test Docs")
    db_session.add(col)
    await db_session.commit()

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}

    return {
        "tenant": tenant,
        "user": user,
        "collection": col,
        "headers": headers,
        "db": db_session,
    }


@pytest.mark.asyncio
@patch("app.api.v1.documents.process_document.delay")
@patch("app.api.v1.documents.storage_service.upload_file")
async def test_document_upload_queues_celery_task(
    mock_upload, mock_delay, client: AsyncClient, setup_document_test
):
    """
    Tests that uploading a document saves to DB, uploads to MinIO, and queues the Celery task.
    """
    col_id = setup_document_test["collection"].id
    headers = setup_document_test["headers"]

    # Mock file upload
    file_content = b"Mock PDF Content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}

    response = await client.post(
        f"/api/v1/collections/{col_id}/documents/upload", files=files, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["message"] == "Document uploaded and processing started"

    # Verify MinIO upload was called
    mock_upload.assert_called_once()

    # Verify Celery task was queued
    mock_delay.assert_called_once()

    # Verify DB state
    db = setup_document_test["db"]
    from sqlalchemy import select

    doc = (
        (
            await db.execute(
                select(Document).where(Document.id == uuid.UUID(data["document_id"]))
            )
        )
        .scalars()
        .first()
    )
    assert doc is not None
    assert doc.status == "processing"


@pytest.mark.asyncio
@patch("app.api.v1.documents.process_document.delay")
async def test_document_retry_failed(
    mock_delay, client: AsyncClient, setup_document_test
):
    """
    Tests that a failed document can be retried, which re-queues the Celery task.
    """
    db = setup_document_test["db"]
    tenant_id = setup_document_test["tenant"].id
    col_id = setup_document_test["collection"].id
    headers = setup_document_test["headers"]

    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        collection_id=col_id,
        original_filename="failed.pdf",
        mime_type="application/pdf",
        file_size=1024,
        storage_path="mock/path",
        status="failed",
        created_by=setup_document_test["user"].id,
    )
    db.add(doc)
    await db.commit()

    response = await client.post(
        f"/api/v1/collections/{col_id}/documents/{doc.id}/retry", headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Retry queued"

    # Verify Celery task was re-queued
    mock_delay.assert_called_once()

    # Verify DB status changed to processing
    await db.refresh(doc)
    assert doc.status == "processing"
