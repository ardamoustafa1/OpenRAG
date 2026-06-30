# OpenRAG Python SDK

The official Python SDK for the [OpenRAG Platform](https://openrag.com).

## Installation

```bash
pip install openrag
```

## Quick Start

```python
from openrag.client import OpenRAGClient

# Initialize the client
client = OpenRAGClient(
    api_key="your_api_key",
    tenant_id="your_tenant_id",
    base_url="https://api.yourdomain.com/api/v1"
)

# 1. Create a Collection
collection = client.create_collection(name="HR Documents")
collection_id = collection["id"]

# 2. Upload a Document
print("Uploading document...")
response = client.upload_document(
    collection_id=collection_id,
    file_path="./employee_handbook.pdf"
)
print(response)

# 3. Stream a Chat Completion
print("Asking a question...")
stream = client.chat_stream(
    collection_id=collection_id,
    prompt="What is the remote work policy?"
)

for chunk in stream:
    if "content" in chunk:
        print(chunk["content"], end="", flush=True)
    if "citations" in chunk:
        print(f"\n[Sources: {chunk['citations']}]")
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```
