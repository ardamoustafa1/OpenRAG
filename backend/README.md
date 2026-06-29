# Enterprise RAG Platform - Backend API

This is the core Python backend for the Enterprise RAG Platform, built with FastAPI, PostgreSQL, Qdrant, and Redis.

## Features
- **FastAPI**: Asynchronous, highly concurrent REST API.
- **Hybrid RAG**: Integrated Dense (Qdrant) and Sparse (BM25 via Redis) Retrieval.
- **Background Tasks**: Celery workers for async document ingestion and chunking.
- **Security**: Argon2/SHA256 hashing, JWT authentication, and TOTP MFA.
- **Multi-Tenant**: Native Row-Level Security (RLS) and vector namespaces.

## Quick Start

### 1. Requirements
- Python 3.12+
- Docker (for dependencies)

### 2. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Database Migrations
Make sure you have an `.env` file at the project root based on `.env.example`.
```bash
alembic upgrade head
```

### 4. Run Locally
```bash
# Start required infra (Postgres, Redis, Qdrant, MinIO)
docker compose up -d postgres redis qdrant minio

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Running Workers
In a separate terminal:
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

## Testing
We use `pytest` and `testcontainers` for robust integration testing.
```bash
pytest tests/
```
