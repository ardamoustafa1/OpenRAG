# Performance Benchmarks & Targets

This document establishes the baseline performance requirements for the Enterprise RAG Platform. Any pull request that degrades these metrics significantly should be flagged for review.

## Environment Specifications
The baselines below assume the following hardware profile (or equivalent cloud instances):
- **API Server:** 4 vCPUs, 8GB RAM
- **Vector Store (Qdrant):** 4 vCPUs, 16GB RAM (Memory-mapped storage)
- **Database (PostgreSQL):** 2 vCPUs, 4GB RAM
- **LLM Engine:** vLLM running on 1x NVIDIA A10G (24GB VRAM)

## Baseline Targets

### 1. Retrieval & Re-ranking (Hybrid Search)
- **P50 Latency:** < 150ms
- **P95 Latency:** < 300ms
- **Target Throughput:** 50 QPS

### 2. Document Ingestion (Async via Celery)
- **Small Documents (< 10 pages, Text/Markdown):** < 2 seconds
- **Large Documents (100+ pages PDF, OCR):** < 45 seconds
- **Target Indexing Speed:** ~1,500 vectors/second (Qdrant bulk upsert)

### 3. LLM Generation (Streaming)
- **Time to First Token (TTFT):** < 400ms
- **Tokens Per Second (TPS):** > 45 TPS (per concurrent user)

### 4. API Endpoints (Auth, Quota, Admin)
- **P99 Latency:** < 50ms (Cache hit) / < 120ms (DB hit)

## Running Load Tests

We use `locust` to simulate concurrent user loads. 
To run a test against the benchmarks:

```bash
cd backend/tests/performance
locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host=http://api.localhost
```

*Note: Ensure your test database is seeded with a representative corpus (~10,000 documents) before running benchmarks to simulate real-world vector index sizes.*
