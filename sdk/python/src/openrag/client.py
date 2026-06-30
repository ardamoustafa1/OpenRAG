import httpx
import json
from typing import Optional, Dict, Any, Generator

class OpenRAGClient:
    """Official OpenRAG Python SDK"""
    
    def __init__(self, api_key: str, tenant_id: str, base_url: str = "https://api.openrag.com/api/v1"):
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Tenant-ID": self.tenant_id
            },
            timeout=30.0
        )

    def _get(self, path: str) -> Dict[str, Any]:
        resp = self.client.get(f"{self.base_url}{path}")
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.client.post(f"{self.base_url}{path}", json=json_data)
        resp.raise_for_status()
        return resp.json()

    def get_collections(self) -> Dict[str, Any]:
        """List all collections available to the tenant."""
        return self._get("/collections")

    def create_collection(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new document collection."""
        return self._post("/collections", {"name": name, "description": description})

    def upload_document(self, collection_id: str, file_path: str) -> Dict[str, Any]:
        """Upload a local file for ingestion."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            resp = self.client.post(f"{self.base_url}/collections/{collection_id}/documents/upload", files=files)
            resp.raise_for_status()
            return resp.json()

    def chat_stream(self, collection_id: str, prompt: str) -> Generator[str, None, None]:
        """Send a prompt and stream the response via SSE."""
        payload = {
            "collection_id": collection_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        with self.client.stream("POST", f"{self.base_url}/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    yield json.loads(data_str)
