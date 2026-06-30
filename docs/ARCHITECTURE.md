# Architecture: Enterprise RAG AI Platform

## 1. High-Level System Architecture

The platform operates as a modular, horizontally scalable microservices ecosystem. It is engineered for true logical multi-tenancy, ensuring data isolation across the entire stack.

```mermaid
graph TD
    Client[Client Browser / SDK] -->|HTTPS / WSS| Ingress[Traefik Ingress Controller]
    
    Ingress -->|REST / SSE| API[FastAPI Backend]
    Ingress -->|Static Assets| Frontend[Next.js Frontend]
    Ingress -->|Monitoring| Grafana[Grafana Dashboard]
    
    API -->|Auth, RBAC, Config| DB[(PostgreSQL + pgvector)]
    API -->|Rate Limiting, Cache| Redis[(Redis Stack)]
    API -->|Dense & Sparse Embeddings| VectorDB[(Qdrant Vector Store)]
    
    API -.->|Enqueue Tasks| CeleryWorker[Celery Worker]
    CeleryWorker -->|Raw Document Storage| Minio[(MinIO Object Storage)]
    CeleryWorker -->|Upsert Chunks| VectorDB
    CeleryWorker -->|Read/Write State| DB
    
    API -->|Context + Prompt| LLM[LiteLLM Proxy]
    LLM --> vLLM[vLLM Inference Engine]
    LLM --> Ollama[Ollama Local Models]
    
    API -.->|Traces & Evals| Langfuse[(Langfuse)]
    API -.->|Metrics| Prom[Prometheus]
    CeleryWorker -.->|Logs| Loki[(Loki Log Aggregator)]
```

## 2. Hybrid RAG Query Flow

Our Retrieval-Augmented Generation pipeline leverages both semantic (Dense) and keyword (Sparse BM25) search for maximum recall.

```mermaid
sequenceDiagram
    participant User as User (Next.js)
    participant API as FastAPI Router
    participant Auth as Auth Middleware
    participant Qdrant as Qdrant (VectorDB)
    participant LLM as LiteLLM / vLLM
    
    User->>API: POST /api/v1/chat (Prompt)
    API->>Auth: Extract X-Tenant-ID & Verify JWT
    Auth-->>API: Tenant Context
    
    API->>LLM: Embed User Prompt
    LLM-->>API: Dense Vector [0.1, 0.4...]
    
    par Dense Search
        API->>Qdrant: Search (Vector + Tenant Filter)
    and Sparse Search
        API->>Qdrant: Search (BM25 Keyword Match)
    end
    
    Qdrant-->>API: Dense Chunks & Sparse Chunks
    
    API->>API: Reciprocal Rank Fusion (RRF) Re-ranking
    API->>API: Construct Context Window
    
    API->>LLM: Stream (Context + System Prompt + User Prompt)
    LLM-->>API: Token Stream
    API-->>User: Server-Sent Events (SSE) Stream
```

## 3. Asynchronous Ingestion Pipeline

Document ingestion is fully decoupled from the API to prevent blocking operations when handling large PDFs or multi-gigabyte archives.

```mermaid
sequenceDiagram
    participant API as API
    participant Minio as MinIO
    participant Redis as Redis Queue
    participant Celery as Celery Worker
    participant Unstructured as Unstructured Parser
    participant LLM as LLM (Embedding)
    participant Qdrant as Qdrant
    
    API->>Minio: Upload Raw PDF
    API->>Redis: Enqueue `process_document(id)`
    API-->>User: HTTP 202 Accepted
    
    Celery->>Redis: Dequeue Job
    Celery->>Minio: Download Raw PDF
    Celery->>Unstructured: OCR & Text Extraction
    Unstructured-->>Celery: Raw Text Elements
    
    Celery->>Celery: Semantic Chunking (LangChain)
    
    loop Batch Embeddings
        Celery->>LLM: Embed Chunks
        LLM-->>Celery: Vectors
    end
    
    Celery->>Qdrant: Bulk Upsert (Vectors + Tenant Metadata)
    Celery->>API: Update Document Status (Success)
```

## 4. Security & Tenant Isolation Model

Security is built into the lowest levels of the architecture. The platform operates on a **Logical Separation** model.

### 4.1 Request Context
Every request passing through Traefik is intercepted by `TenantMiddleware` in FastAPI. This middleware extracts the `X-Tenant-ID` (or infers it from the subdomain) and binds it to a `ContextVar`. Every subsequent database or cache operation is inherently filtered by this context.

### 4.2 Row-Level Security (PostgreSQL)
PostgreSQL schemas leverage SQLAlchemy global filters to ensure a query for `Document.select()` implicitly appends `WHERE tenant_id = current_tenant`.

### 4.3 Vector Isolation (Qdrant)
Qdrant does not support true database-level multi-tenancy in the open-source version. To compensate, all vector upserts and search payloads strictly inject `{ "tenant_id": "uuid" }` into the Qdrant `payload`. The search wrapper enforces a mandatory `Must` filter condition on this key, guaranteeing tenant isolation at the index level.

### 4.4 Air-gapped AI
By utilizing local models via `vLLM` and `Ollama`, no prompts or retrieved context ever leave the VPC. The `LiteLLM` proxy acts as an internal firewall, capable of masking PII before sending it to the model layer (if configured).
