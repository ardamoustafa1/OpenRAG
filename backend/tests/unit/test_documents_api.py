import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_tenant, get_current_user, get_db_session
from app.main import app

pytestmark = pytest.mark.asyncio


@patch("app.api.v1.documents.process_document")
async def test_upload_document(
    mock_process, mock_db_session, mock_current_user, mock_current_tenant
):
    collection_id = uuid.uuid4()
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = (
        SimpleNamespace(id=collection_id)
    )

    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant

    # Needs a mock upload file
    files = {"file": ("test.txt", b"Hello world", "text/plain")}

    # Mocking storage_service is also required for real upload,
    # but the endpoint handles DB save and kicks off Celery task.
    with patch("app.api.v1.documents.storage_service.upload_file") as mock_storage:
        mock_storage.return_value = None
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/collections/{collection_id}/documents/upload",
                files=files,
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Document uploaded and processing started"
        assert "document_id" in response.json()

        # Verify Celery task was called
        mock_process.delay.assert_called_once()

    app.dependency_overrides.clear()
