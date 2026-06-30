# Quickstart Guide 🚀

Welcome to the Enterprise RAG AI Platform! This guide will help you set up the platform locally and ingest your first document.

## 1. Prerequisites

- **Docker & Docker Compose** (v2.0+)
- **Minimum 16GB RAM** (If you plan to run local LLMs like vLLM or Ollama)
- **Make** (Optional but recommended)

## 2. Configuration

Clone the repository and set up your environment variables:

```bash
git clone https://github.com/ardamoustafa1/OpenRAG.git
cd OpenRAG

cp .env.example .env
```

Open `.env` and fill in the required secrets (generate them using `openssl rand -hex 32`):
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`
- `LANGFUSE_NEXTAUTH_SECRET`
- `LANGFUSE_SALT`
- `TRAEFIK_DASHBOARD_CREDENTIALS`

## 3. Starting the Platform

Boot the entire stack (16 containers) in detached mode:

```bash
make up
```
*(Alternatively: `docker compose up -d`)*

Wait a few seconds for Postgres to initialize, then run database migrations:

> [!IMPORTANT]
> **MANDATORY STEP:** You must run database migrations to create the schemas before attempting to access the backend or UI.

```bash
make migrate
```

## 4. Accessing the UI

- **Frontend:** http://localhost:3000
- **API Docs:** http://api.localhost/docs
- **Traefik Dashboard:** http://localhost:8080
- **Grafana:** http://grafana.localhost

> **Login:** Use the UI to sign up as the first admin, or log in via your configured Azure AD / SAML provider.

## 5. Ingesting Your First Document

1. Log into the Frontend at http://localhost:3000.
2. Navigate to **Admin -> Documents**.
3. Create a new **Collection** (e.g., "HR Policies").
4. Drag and drop a PDF file into the upload zone.
5. The document will be asynchronously chunked, embedded, and saved to Qdrant.
6. Navigate to **Chat**, select your collection, and start asking questions!
