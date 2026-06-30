import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import get_current_user, get_db_session, get_current_tenant

pytestmark = pytest.mark.asyncio

@patch("app.api.v1.documents.process_document")
async def test_upload_document(mock_process, mock_db_session, mock_current_user, mock_current_tenant):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant
    
    # Needs a mock upload file
    files = {"file": ("test.txt", b"Hello world", "text/plain")}
    data = {"collection_id": "test-collection"}
    
    # Mocking storage_service is also required for real upload, 
    # but the endpoint handles DB save and kicks off Celery task.
    with patch("app.api.v1.documents.storage_service.upload_file") as mock_storage:
        mock_storage.return_value = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/documents", files=files, data=data)
            
        assert response.status_code == 200
        assert response.json()["filename"] == "test.txt"
        assert response.json()["status"] == "processing"
        
        # Verify Celery task was called
        mock_process.delay.assert_called_once()
        
    app.dependency_overrides.clear()
