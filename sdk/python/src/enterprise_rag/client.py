import httpx
from typing import Optional
from .chat import ChatClient
from .documents import DocumentsClient

class EnterpriseRAGClient:
    """Main client for interacting with the Enterprise RAG API."""
    
    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        base_url: str = "http://localhost:8000/api/v1",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.base_url = base_url.rstrip("/")
        
        self._http_client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Tenant-ID": self.tenant_id,
                "Content-Type": "application/json"
            },
            timeout=timeout
        )
        
        # Attach sub-clients
        self.chat = ChatClient(self._http_client)
        self.documents = DocumentsClient(self._http_client)

    def close(self):
        self._http_client.close()

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
