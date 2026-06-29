import httpx
from typing import Iterator, Dict, Any

class ChatClient:
    """Client for chat operations."""
    
    def __init__(self, http_client: httpx.Client):
        self._client = http_client

    def send_message(self, conversation_id: str, content: str, collection_id: str) -> Dict[str, Any]:
        """Send a message synchronously and wait for full response."""
        resp = self._client.post(
            f"/conversations/{conversation_id}/messages",
            json={"content": content, "collection_id": collection_id}
        )
        resp.raise_for_status()
        return resp.json()
        
    def stream_message(self, conversation_id: str, content: str, collection_id: str) -> Iterator[str]:
        """Send a message and stream the SSE response."""
        with self._client.stream(
            "POST",
            f"/conversations/{conversation_id}/messages",
            json={"content": content, "collection_id": collection_id}
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]
