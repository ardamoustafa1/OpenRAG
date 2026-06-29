# Environment Variables Reference

This document explains all the environment variables used in the Enterprise RAG Platform.

## Core Settings

| Variable | Description | Default / Example | Required |
|----------|-------------|-------------------|----------|
| `ENVIRONMENT` | Running environment (e.g., `development`, `production`). In production, Swagger docs are disabled. | `production` | Yes |
| `SECRET_KEY` | Cryptographic key used to sign JWTs. Must be a 32+ byte random string. | - | **Yes** |
| `CORS_ALLOW_ORIGINS` | JSON array of allowed origins for cross-origin requests. | `["https://app.yourdomain.com"]` | Yes |
| `LOG_LEVEL` | Application logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `INFO` | No |

## Infrastructure Connection Strings

| Variable | Description | Default / Example | Required |
|----------|-------------|-------------------|----------|
| `DATABASE_URL` | Asyncpg connection string to PostgreSQL. | `postgresql+asyncpg://postgres:postgres@postgres:5432/rag_db` | Yes |
| `REDIS_URL` | Connection string to Redis (used for queues, cache, and token blacklisting). | `redis://redis:6379/0` | Yes |
| `QDRANT_URL` | URL to Qdrant vector database. | `http://qdrant:6333` | Yes |
| `MINIO_ENDPOINT` | URL to MinIO API endpoint. | `minio:9000` | Yes |

## Storage Credentials (MinIO)

| Variable | Description | Default / Example | Required |
|----------|-------------|-------------------|----------|
| `MINIO_ACCESS_KEY` | Access key for MinIO. | - | Yes |
| `MINIO_SECRET_KEY` | Secret key for MinIO. | - | Yes |
| `STORAGE_BUCKET_NAME`| Default bucket for document uploads. | `rag-documents` | No |

## LLM Integration

| Variable | Description | Default / Example | Required |
|----------|-------------|-------------------|----------|
| `LITELLM_BASE_URL` | Endpoint for LiteLLM proxy. | `http://litellm:4000` | Yes |
| `OLLAMA_BASE_URL` | Endpoint for local Ollama instance (fallback). | `http://ollama:11434` | No |
| `OPENAI_API_KEY` | (Optional) Used if routing specific queries to OpenAI via LiteLLM. | - | No |

## Billing & Integrations (Optional)

| Variable | Description | Default / Example | Required |
|----------|-------------|-------------------|----------|
| `STRIPE_API_KEY` | Secret key for Stripe API. | `sk_test_...` | No |
| `STRIPE_WEBHOOK_SECRET`| Secret used to verify Stripe webhook signatures. | `whsec_...` | No |
