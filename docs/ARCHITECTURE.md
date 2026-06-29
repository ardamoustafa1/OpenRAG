# Architecture: Enterprise RAG AI Platform

## 1. System Components

The platform is designed as a modular, containerized microservices architecture to ensure high availability, security, and true multi-tenancy.

### 1.1 Core Backend (FastAPI)
- **Framework:** FastAPI (Python 3.12+)
- **Purpose:** Handles all API requests, authentication, and orchestrates the RAG pipeline.
- **Scaling:** Can be scaled horizontally via Kubernetes HPA.

### 1.2 Frontend (Next.js)
- **Framework:** Next.js (React)
- **Purpose:** Delivers a responsive, WAI-ARIA compliant, dark-mode optimized user interface. Uses `@tanstack/react-query` for real-time state management.

### 1.3 Data & Storage Layer
- **PostgreSQL (pgvector):** Stores relational data (Users, Tenants, Billing, Audit Logs).
- **Qdrant:** Highly optimized Vector Database storing document embeddings for dense retrieval.
- **MinIO:** S3-compatible object storage holding raw uploaded documents before ingestion.
- **Redis:** Acts as the Celery message broker, caches temporary data, and maintains rate limiting states.

### 1.4 Background Processing (Celery)
- **Purpose:** Handles asynchronous document parsing, chunking (via `unstructured`), and embedding generation to prevent blocking the API.

### 1.5 LLM Orchestration
- **vLLM / Ollama:** Local inference engines executing generative requests.
- **LiteLLM:** A proxy layer managing model routing and fallback mechanisms.

## 2. Request Flow (Chat)

1. **Client Request:** User sends a prompt via Next.js UI.
2. **Gateway:** Traefik routes the request to the FastAPI backend.
3. **Authentication:** `TenantMiddleware` extracts the tenant context. User JWT is verified.
4. **Vector Retrieval:** Backend queries Qdrant for semantic similarity (Dense search).
5. **Context Building:** Retrieved chunks are reranked and packaged into a unified context window.
6. **Generation:** Prompt + Context is forwarded to LiteLLM -> vLLM.
7. **Streaming:** SSE stream is established, piping tokens back to the client in real-time.

## 3. Security Architecture
- **Strict Network Policies:** Kubernetes Calico rules block all direct access to databases.
- **Secrets Management:** Bitnami Sealed Secrets manage production credentials.
- **Per-Tenant Rate Limiting:** Enforced via `slowapi` utilizing the unique `tenant_id`.
