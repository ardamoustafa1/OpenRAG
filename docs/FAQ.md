# ❓ Frequently Asked Questions — OpenRAG

## General

### What is OpenRAG?

OpenRAG is a 100% on-premise, multi-tenant Retrieval-Augmented Generation (RAG) platform built for enterprises that cannot compromise on data privacy. It combines a FastAPI backend, Next.js frontend, and a full stack of local AI inference tools (vLLM/Ollama via LiteLLM) so that **no data ever leaves your infrastructure**.

---

### How is OpenRAG different from LangChain, Dify, or PrivateGPT?

| | OpenRAG | LangChain | Dify | PrivateGPT |
|--|---------|-----------|------|------------|
| 100% On-Premise | ✅ | Partial | Partial | ✅ |
| Multi-Tenancy | ✅ Native | ❌ | Workspaces | ❌ |
| Hybrid Retrieval (Dense+BM25+RRF) | ✅ | Manual | Limited | ❌ |
| MFA / SSO | ✅ Built-in | ❌ | Limited | ❌ |
| Kubernetes / Helm | ✅ Native | ❌ | Limited | ❌ |
| Production Observability | ✅ Full stack | ❌ | Partial | ❌ |

---

### Do I need a GPU?

No. OpenRAG works fully on CPU using **Ollama** for local inference. However, GPU (NVIDIA) is **strongly recommended** for production workloads using `vLLM` for optimal throughput. A minimum of 16GB RAM is required; 32GB+ is recommended for running local LLMs alongside all services.

---

### Can I use external LLMs (OpenAI, Anthropic, etc.)?

Yes. The **LiteLLM proxy** supports 100+ providers. Simply configure `litellm/config.yaml` with your preferred model. Note that using external providers means prompts leave your infrastructure — which may not be acceptable for air-gapped deployments.

---

## Data & Privacy

### Does OpenRAG send any telemetry?

**Absolutely not.** Zero telemetry is a core design principle. The platform:
- Does not phone home to any external service
- Langfuse is self-hosted (or optional)
- All metrics stay within your Prometheus/Grafana stack

---

### How is multi-tenancy enforced?

Tenant isolation is enforced at **three levels**:

1. **Request level**: `TenantMiddleware` extracts `X-Tenant-ID` from every request and binds it to a thread-local context variable.
2. **Database level**: All SQLAlchemy queries implicitly filter by `tenant_id` via global query filters.
3. **Vector level**: Qdrant enforces a mandatory `tenant_id` payload filter on every search query.

A tenant can never see another tenant's documents, chat history, or configurations.

---

### Where are documents stored?

Raw documents (PDFs, DOCX, etc.) are stored in **MinIO** (S3-compatible, fully local). Processed text chunks and their embeddings are stored in **Qdrant**. Document metadata (status, ownership) is stored in **PostgreSQL**. All storage is within your Docker volumes.

---

## Installation & Operations

### How do I add a new LLM model?

Edit `infra/litellm/config.yaml` and add your model under the `model_list` section:

```yaml
model_list:
  - model_name: my-model
    litellm_params:
      model: ollama/llama3.2
      api_base: http://ollama:11434
```

Then restart LiteLLM: `docker compose restart litellm`

---

### How do I run database migrations?

```bash
# Run all pending migrations
make migrate

# Or directly:
docker compose exec backend alembic upgrade head
```

To create a new migration after changing SQLAlchemy models:
```bash
make migrate-create MSG="add_new_column_to_documents"
```

---

### How do I back up my data?

For Docker Compose deployments:
```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U postgres rag_db > backup.sql

# Backup Qdrant (copy volume data)
docker run --volumes-from openrag-qdrant-1 -v $(pwd):/backup ubuntu \
  tar czf /backup/qdrant-backup.tar.gz /qdrant/storage

# Backup MinIO
# Access the MinIO console at http://localhost:9001 and use the built-in export tool
```

For Kubernetes, see `infra/backup/` for automated CronJob backup scripts.

---

### How do I scale for high traffic?

Scale the backend API horizontally:
```bash
docker compose up -d --scale backend=3
```

Or via Kubernetes HPA (already configured in `infra/helm/`):
```bash
kubectl apply -f infra/helm/hpa.yaml
```

The Celery workers can also be scaled independently:
```bash
docker compose up -d --scale celery_worker=5
```

---

### How do I update OpenRAG to a new version?

```bash
# Pull latest changes
git pull origin main

# Rebuild images
make build

# Apply any new migrations
make migrate

# Restart services
make restart
```

---

## Security

### How are passwords stored?

Passwords are hashed using **Argon2id** — the winner of the Password Hashing Competition and the current industry gold standard. API keys are hashed with SHA-256 (faster for high-throughput key validation without DoS risk).

### How are JWT tokens secured?

- **Signed** with HMAC-SHA256 using a 256-bit `SECRET_KEY`
- **Refresh token rotation**: old refresh tokens are immediately blacklisted in Redis on each use
- **Token blacklist**: stored as SHA-256 hashes in Redis with TTL matching token expiry
- **MFA**: TOTP (RFC 6238) with ±30 second window tolerance

### How do I report a security vulnerability?

Please **do not** open a public GitHub issue. Use [GitHub's private advisory system](https://github.com/ardamoustafa1/OpenRAG/security/advisories/new) or email `security@openrag.com`. See [SECURITY.md](../SECURITY.md) for our full disclosure policy.

---

## Development & Contributing

### How do I set up a local development environment?

```bash
# Clone and setup
git clone https://github.com/ardamoustafa1/OpenRAG.git && cd OpenRAG
cp .env.example .env
# Edit .env to set SECRET_KEY and other required values

# Start all services
make up

# Run migrations
make migrate

# Watch logs
make logs
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full development setup instructions.

---

### What is the test coverage requirement for PRs?

All PRs must maintain **≥80% backend test coverage**. The CI pipeline enforces this automatically. Run tests locally with:
```bash
make test-unit
```

---

### Is there a roadmap?

Yes. See [ROADMAP.md](../ROADMAP.md) for planned features. You can influence prioritization by upvoting [feature requests](https://github.com/ardamoustafa1/OpenRAG/issues?q=label%3Afeature-request) or opening a [GitHub Discussion](https://github.com/ardamoustafa1/OpenRAG/discussions).
