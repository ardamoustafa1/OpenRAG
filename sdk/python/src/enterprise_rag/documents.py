import httpx
from typing import Dict, Any, BinaryIO

class DocumentsClient:
    """Client for document ingestion and management."""
    
    def __init__(self, http_client: httpx.Client):
        self._client = http_client

    def upload_document(self, collection_id: str, file_name: str, file_content: BinaryIO) -> Dict[str, Any]:
        """Upload a document to a specific collection."""
        # Note: We need to override the default JSON content type for multipart uploads
        headers = self._client.headers.copy()
        headers.pop("Content-Type", None)
        
        files = {"file": (file_name, file_content)}
        
        resp = self._client.post(
            f"/collections/{collection_id}/documents/upload",
            files=files,
            headers=headers
        )
        resp.raise_for_status()
        return resp.json()
        
    def list_documents(self, collection_id: str) -> list[Dict[str, Any]]:
        """List documents in a collection."""
        resp = self._client.get(f"/collections/{collection_id}/documents")
        resp.raise_for_status()
        return resp.json()
