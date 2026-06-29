# Enterprise RAG AI Platform - Python SDK

A robust, enterprise-grade Python SDK for integrating with the RAG AI Platform.

## Features
- **Sync & Async** fully supported.
- **Streaming** interface for real-time generative responses.
- **Automatic Exponential Backoff** for rate limits (`429`) and transient network errors.

## Installation

```bash
pip install enterprise-rag-sdk
```

## Quickstart

```python
from ai_platform import AIPlatformClient

# Initialize
client = AIPlatformClient(api_key="your_api_key", tenant_url="https://api.yourdomain.com")

# Standard Chat
response = client.chat(
    query="What is our security policy?",
    collection_ids=["col-1234"]
)
print(response)

# Streaming Chat
for chunk in client.stream_chat(query="Explain the Q3 report.", collection_ids=["col-1234"]):
    print(chunk.content, end="", flush=True)

client.close()
```

## Async Usage

```python
import asyncio
from ai_platform import AIPlatformClient

async def main():
    client = AIPlatformClient(api_key="your_api_key", tenant_url="https://api.yourdomain.com")
    
    response = await client.achat("Hi", ["col-123"])
    print(response)
    
    async for chunk in client.astream_chat("Explain Q3", ["col-123"]):
        print(chunk.content, end="", flush=True)

    await client.aclose()

asyncio.run(main())
```
