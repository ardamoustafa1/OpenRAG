import httpx
import json
from typing import Generator, AsyncGenerator, Any, Optional
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ChatChunk(BaseModel):
    content: str
    sources: Optional[list] = None

class Document(BaseModel):
    id: str
    filename: str
    status: str
    tenant_id: str

class OpenRAGError(Exception):
    """Base exception for OpenRAG SDK"""
    pass

class RateLimitError(OpenRAGError):
    pass

class AuthError(OpenRAGError):
    pass

class APIError(OpenRAGError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


def _should_retry_error(exception: BaseException) -> bool:
    """Retry on RateLimitError or specific httpx exceptions."""
    if isinstance(exception, RateLimitError):
        return True
    if isinstance(exception, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError)):
        return True
    return False


class AIPlatformClient:
    """
    Enterprise RAG AI Platform Python SDK.
    Handles sync/async communication, exponential backoff, and streaming.
    """
    def __init__(self, api_key: str, tenant_url: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = tenant_url.rstrip("/")
        self.timeout = timeout
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenRAG-Python-SDK/1.0"
        }
        
        self.client = httpx.Client(headers=self.headers, timeout=self.timeout)
        self.aclient = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)

    def _handle_error(self, response: httpx.Response):
        if 200 <= response.status_code < 300:
            return
        if response.status_code == 429:
            raise RateLimitError("RateLimitExceeded: " + response.text)
        elif response.status_code in (401, 403):
            raise AuthError("AuthError: Invalid or unauthorized API Key")
        else:
            raise APIError(response.status_code, response.text)

    # --- Chat Endpoints ---

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def chat(self, query: str, collection_ids: list[str]) -> dict:
        """Synchronous standard chat."""
        payload = {"query": query, "collections": collection_ids}
        response = self.client.post(f"{self.base_url}/api/v1/chat", json=payload)
        self._handle_error(response)
        return response.json()

    def stream_chat(self, query: str, collection_ids: list[str]) -> Generator[ChatChunk, None, None]:
        """Synchronous streaming chat."""
        payload = {"query": query, "collections": collection_ids, "stream": True}
        
        with self.client.stream("POST", f"{self.base_url}/api/v1/chat/stream", json=payload) as response:
            self._handle_error(response)
            for line in response.iter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    if data:
                        parsed = json.loads(data)
                        yield ChatChunk(**parsed)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    async def achat(self, query: str, collection_ids: list[str]) -> dict:
        """Asynchronous standard chat."""
        payload = {"query": query, "collections": collection_ids}
        response = await self.aclient.post(f"{self.base_url}/api/v1/chat", json=payload)
        self._handle_error(response)
        return response.json()

    async def astream_chat(self, query: str, collection_ids: list[str]) -> AsyncGenerator[ChatChunk, None]:
        """Asynchronous streaming chat."""
        payload = {"query": query, "collections": collection_ids, "stream": True}
        
        async with self.aclient.stream("POST", f"{self.base_url}/api/v1/chat/stream", json=payload) as response:
            self._handle_error(response)
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    if data:
                        parsed = json.loads(data)
                        yield ChatChunk(**parsed)

    # --- Document Management Endpoints ---

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def list_documents(self, skip: int = 0, limit: int = 100) -> list[Document]:
        """List documents with pagination."""
        response = self.client.get(f"{self.base_url}/api/v1/documents", params={"skip": skip, "limit": limit})
        self._handle_error(response)
        return [Document(**doc) for doc in response.json()]
        
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    async def alist_documents(self, skip: int = 0, limit: int = 100) -> list[Document]:
        """Async list documents with pagination."""
        response = await self.aclient.get(f"{self.base_url}/api/v1/documents", params={"skip": skip, "limit": limit})
        self._handle_error(response)
        return [Document(**doc) for doc in response.json()]

    # --- Cleanup ---

    def close(self):
        self.client.close()
        
    async def aclose(self):
        await self.aclient.aclose()

