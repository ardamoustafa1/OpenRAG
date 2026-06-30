# Enterprise RAG Platform - Helm Charts

This directory contains the Kubernetes Helm charts for deploying the Enterprise RAG Platform in a production-grade, highly available setup.

## Prerequisites
- Kubernetes 1.25+
- Helm 3.0+
- Ingress controller (e.g., NGINX, Traefik)
- PV provisioner support in the underlying infrastructure

## Components Installed
This chart will deploy:
- FastAPI Backend (Deployment + HPA)
- Next.js Frontend (Deployment)
- Celery Workers (Deployment)
- Qdrant (StatefulSet)
- PostgreSQL (StatefulSet / Bitnami subchart)
- Redis (StatefulSet / Bitnami subchart)
- MinIO (StatefulSet / Bitnami subchart)

## Quick Start

### 1. Add Dependencies
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm dependency update
```

### 2. Configure Values
Copy `values.yaml` to `custom-values.yaml` and configure your domain, TLS secrets, and resource limits.
```bash
cp values.yaml custom-values.yaml
# Edit custom-values.yaml
```

### 3. Deploy
```bash
helm install OpenRAG . -f custom-values.yaml --namespace rag-platform --create-namespace
```

## Production Recommendations
- **Externalize DBs**: For enterprise production, disable the bundled PostgreSQL, Redis, and MinIO charts and provide connection strings to managed services (e.g., AWS RDS, ElastiCache, S3).
- **GPU Nodes**: Assign Celery workers running local LLMs to GPU-enabled node pools using `nodeSelector` and `tolerations`.
- **Secrets Management**: Do not store secrets in `values.yaml`. Use External-Secrets operator or HashiCorp Vault injector to map secrets into the pods.
