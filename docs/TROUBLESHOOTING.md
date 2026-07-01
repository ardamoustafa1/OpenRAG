# 🛠️ Troubleshooting Guide — OpenRAG

This guide covers the most common issues you'll encounter when setting up or operating OpenRAG.

---

## 🚀 Startup Issues

### `SECRET_KEY must be set` error on startup

**Symptom**: `docker compose up` fails with validation error.

**Cause**: `SECRET_KEY` is a required field with no default.

**Fix**:
```bash
# Generate a secure key
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

---

### Backend exits with `Connection refused` to PostgreSQL

**Symptom**: Backend container starts then immediately exits.

**Cause**: PostgreSQL hasn't finished initializing before backend starts.

**Fix**: The `depends_on: condition: service_healthy` in `docker-compose.yml` handles this automatically. If it persists:
```bash
# Wait for postgres then restart backend
docker compose restart backend
# Or watch the healthcheck
docker compose ps
```

---

### `GRAFANA_ADMIN_PASSWORD must be set` error

**Cause**: Grafana requires a non-empty admin password defined in `.env`.

**Fix**:
```bash
echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16)" >> .env
```

---

### Langfuse fails to start

**Symptom**: `langfuse` container exits with database error.

**Cause**: `LANGFUSE_NEXTAUTH_SECRET` and `LANGFUSE_SALT` must be set.

**Fix**:
```bash
echo "LANGFUSE_NEXTAUTH_SECRET=$(openssl rand -hex 32)" >> .env
echo "LANGFUSE_SALT=$(openssl rand -hex 32)" >> .env
docker compose restart langfuse
```

---

## 📄 Document Ingestion Issues

### Document stuck in "Processing" status

**Cause**: Celery worker is not running, or the task failed silently.

**Debug**:
```bash
# Check celery worker logs
docker compose logs -f celery_worker

# Check Flower dashboard for failed tasks
open http://flower.localhost
```

**Common root causes**:
- MinIO bucket doesn't exist (run `make migrate` to auto-provision)
- Qdrant collection not initialized — check `qdrant` logs
- Out of memory during PDF OCR — increase Docker memory limit

---

### PDF upload returns 500 error

**Cause**: `tesseract-ocr` or `poppler-utils` not installed in the container.

**Fix**: The `backend/Dockerfile` includes these. Rebuild the image:
```bash
make build-backend
docker compose up -d backend
```

---

## 🔍 RAG / Retrieval Issues

### Chat returns "No relevant documents found"

**Possible causes**:
1. **Collection empty** — documents haven't been indexed yet.
2. **Wrong tenant/collection ID** — verify the `X-Tenant-ID` header.
3. **BM25 index not built** — sparse search needs at least one ingestion cycle.

**Debug**:
```bash
# Check vector count in Qdrant
curl http://localhost:6333/collections/<collection_name>

# Check BM25 index key in Redis
docker compose exec redis redis-cli keys "bm25:*"
```

---

### Slow retrieval (>500ms)

**Likely causes**:
- Qdrant running without memory-mapped storage (default in dev)
- No GPU for reranker model

**Fix**: Ensure `qdrant_data` volume is on fast SSD. For production, configure Qdrant's `storage.on_disk_payload: true` in `infra/qdrant/config.yaml`.

---

## 🔐 Authentication Issues

### JWT token always invalid after server restart

**Cause**: `SECRET_KEY` is not persisted between restarts (was generated in-memory).

**Fix**: Ensure `SECRET_KEY` is set in `.env` and not regenerated on every startup.

---

### MFA TOTP code rejected

**Cause**: Clock skew between client and server (>30 seconds drift).

**Fix**: Ensure NTP sync on the server:
```bash
sudo ntpdate pool.ntp.org
```

The TOTP validator already uses `valid_window=1` (±30 seconds tolerance).

---

### SSO / SAML login redirect fails

**Cause**: Entity ID or ACS URL mismatch.

**Fix**: Verify your IdP configuration matches:
- **Entity ID**: `https://<your-domain>/api/v1/auth/saml/metadata`
- **ACS URL**: `https://<your-domain>/api/v1/auth/saml/acs`

---

## 📊 Observability Issues

### Grafana shows "No data" in dashboards

**Cause**: Prometheus scrape target not reachable.

**Debug**:
```bash
# Check scrape targets
open http://localhost:9090/targets
```

**Fix**: Ensure backend `/metrics` endpoint is accessible:
```bash
curl http://api.localhost/metrics
```

---

### Langfuse traces not appearing

**Cause**: `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` not set.

**Fix**: Create a project in Langfuse UI (`http://langfuse.localhost`), copy the keys, and add to `.env`:
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```
Then restart backend and celery workers.

---

## 🐳 Docker / Infrastructure Issues

### `docker compose up` fails on Apple Silicon (M1/M2/M3)

**Cause**: Some images are not pre-built for `linux/arm64`.

**Fix**: Force platform emulation:
```bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker compose up -d
```

Or use the native ARM images by setting `platform: linux/arm64/v8` in `docker-compose.yml` for affected services.

---

### Volumes use too much disk space

**Diagnostic**:
```bash
docker system df
docker volume ls
```

**Cleanup** (⚠️ destroys all data):
```bash
make down-clean
```

---

## 🔧 Development Issues

### Hot-reload not working for backend

The backend in `docker-compose.yml` uses `--reload` and mounts `./backend:/app`. Ensure volume mount is correct:
```bash
docker compose logs backend | grep "Reload"
```

If not hot-reloading, restart:
```bash
docker compose restart backend
```

---

### Frontend TypeScript errors after pulling changes

```bash
cd frontend
npm ci  # reinstall exact locked versions
npx tsc --noEmit  # check for type errors
```

---

## 💬 Still Stuck?

1. Check [GitHub Discussions](https://github.com/ardamoustafa1/OpenRAG/discussions) — your question may already be answered.
2. Open a [GitHub Issue](https://github.com/ardamoustafa1/OpenRAG/issues/new/choose) with logs attached.
3. For security issues, use [private advisories](https://github.com/ardamoustafa1/OpenRAG/security/advisories/new).
