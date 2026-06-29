import httpx
import json
import time
from typing import Generator, AsyncGenerator, Any, Optional
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class SDKError(Exception):
    pass

class RateLimitError(SDKError):
    pass

class AuthError(SDKError):
    pass

class ChatChunk(BaseModel):
    content: str
    sources: Optional[list] = None

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
            "User-Agent": "AIPlatform-Python-SDK/1.0"
        }
        
        self.client = httpx.Client(headers=self.headers, timeout=self.timeout)
        self.aclient = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)

    def _handle_error(self, response: httpx.Response):
        if response.status_code == 429:
            raise RateLimitError("RateLimitExceeded: " + response.text)
        elif response.status_code == 401:
            raise AuthError("AuthError: Invalid API Key")
        elif response.status_code >= 400:
            raise SDKError(f"APIError [{response.status_code}]: {response.text}")

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, httpx.RequestError))
    )
    def chat(self, query: str, collection_ids: list[str]) -> dict:
        """Synchronous standard chat."""
        payload = {"query": query, "collections": collection_ids}
        response = self.client.post(f"{self.base_url}/api/v1/chat", json=payload)
        self._handle_error(response)
        return response.json()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, httpx.RequestError))
    )
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
                    parsed = json.loads(data)
                    yield ChatChunk(**parsed)

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, httpx.RequestError))
    )
    async def achat(self, query: str, collection_ids: list[str]) -> dict:
        """Asynchronous standard chat."""
        payload = {"query": query, "collections": collection_ids}
        response = await self.aclient.post(f"{self.base_url}/api/v1/chat", json=payload)
        self._handle_error(response)
        return response.json()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, httpx.RequestError))
    )
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
                    parsed = json.loads(data)
                    yield ChatChunk(**parsed)

    def close(self):
        self.client.close()
        
    async def aclose(self):
        await self.aclient.aclose()
