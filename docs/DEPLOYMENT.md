# Deployment Guide

The Enterprise RAG Platform is designed to be deployed in air-gapped, on-premise environments.

## Deployment Options

### 1. Docker Compose (Single Node)
Best for PoCs, small internal tools, or limited compute environments.
- **Hardware**: Minimum 4 CPU cores, 16GB RAM. If running local LLMs (Ollama/vLLM), a dedicated NVIDIA GPU (minimum 16GB VRAM) is highly recommended.
- **Setup**:
  ```bash
  cp .env.example .env
  # Configure your secrets
  docker compose up -d
  ```

### 2. Kubernetes via Helm (Highly Available)
Best for production enterprise usage requiring scale and failover.
- **Requirements**: K8s cluster, Ingress controller, Persistent Volumes.
- **Setup**: Refer to `infra/helm/README.md`.

## Data Backup and Disaster Recovery

### PostgreSQL
Contains users, tenants, API keys, chat history, and document metadata.
- **Backup**: Run `pg_dump` via a cronjob. If using managed RDS, enable automated snapshots.
- **Restore**: Use `pg_restore`.

### Qdrant
Contains vector embeddings. Loss of this means documents must be re-ingested.
- **Backup**: Enable snapshotting in Qdrant API or backup the volume `/qdrant/storage`.

### MinIO
Contains raw uploaded files (PDFs, docs).
- **Backup**: Use `mc mirror` to continuously replicate to a backup bucket/site.

## Upgrading the Platform
1. Update your `.env` variables if new ones were introduced (check CHANGELOG).
2. Pull the latest Docker images.
3. Run Alembic migrations **before** starting the backend:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
4. Restart services.
