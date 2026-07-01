# 🚀 Getting Started with OpenRAG

Welcome to OpenRAG! This guide will take you from zero to a fully functioning on-premise Enterprise AI Platform in under 10 minutes.

## Prerequisites

- **OS**: Linux, macOS (M1/M2/M3), or Windows (WSL2)
- **Docker & Docker Compose**: v2.20+
- **Python**: 3.12+
- **Hardware**: Minimum 16GB RAM. (32GB+ recommended for running large models locally).
- **GPU (Optional)**: NVIDIA GPU for fast local inference via vLLM.

---

## 1. Installation

Clone the repository and configure your environment:

```bash
git clone https://github.com/ardamoustafa1/OpenRAG.git
cd OpenRAG

# Run the automated setup script
./install.sh
```

If you prefer to configure it manually:
```bash
cp .env.example .env
# Edit .env and generate strong secrets:
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

## 2. Start the Stack

OpenRAG runs 16 microservices in a single `docker-compose.yml`.

```bash
make up
```

Wait about 30 seconds for Qdrant, Postgres, and MinIO to initialize. You can check the health of the services using:
```bash
docker compose ps
```

## 3. Database Initialization

Run the initial database migrations to create the required tables:

```bash
make migrate
```

## 4. Accessing the Platform

- **Frontend (Chat & Admin UI)**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://api.localhost/docs](http://api.localhost/docs)
- **Grafana Dashboards**: [http://grafana.localhost](http://grafana.localhost) (Check `.env` for your admin password)
- **Langfuse Tracing**: [http://langfuse.localhost](http://langfuse.localhost)
- **Traefik Dashboard**: [http://traefik.localhost/dashboard/](http://traefik.localhost/dashboard/)

## 5. Your First RAG Query

1. Go to `http://localhost:3000` and register an admin account.
2. Navigate to the **Knowledge Base** tab and upload a PDF document.
3. Wait a few seconds for the document to be processed (chunked and embedded).
4. Go to the **Chat** tab and ask a question about your document!

## Next Steps

- **Add Custom Models**: Read [Custom Models Guide](CUSTOM_MODELS.md) to integrate Llama 3 or external APIs.
- **Configure Tenants**: Read [Multi-Tenant Setup](MULTI_TENANT_SETUP.md) for isolating data between departments or clients.
- **Troubleshooting**: Check the [Troubleshooting Guide](TROUBLESHOOTING.md) if you encounter any issues.
