# Enterprise AI Platform: Infrastructure & Resource Guidelines

This directory contains the Helm charts, GitOps pipelines, backup strategies, and on-premise installation scripts for the platform.

## Resource Request/Limit Recommendations

Ensure your Kubernetes nodes meet the following compute and memory thresholds to guarantee stability and performance.

| Service | Environment | CPU Request/Limit | RAM Request/Limit | Notes / Autoscaling |
|---------|-------------|--------------------|-------------------|---------------------|
| **Backend** | Dev | 1 / 2 | 2Gi / 4Gi | Min 1 Replica |
| **Backend** | Prod | 2 / 4 | 4Gi / 8Gi | HPA: 3-15 Replicas (Target 75% CPU) |
| **Frontend** | Dev | 500m / 1 | 1Gi / 2Gi | Server-Side Rendering |
| **Frontend** | Prod | 1 / 2 | 2Gi / 4Gi | HPA: 2-10 Replicas |
| **Celery Worker** | Dev | 1 / 2 | 2Gi / 4Gi | Ingestion & Vectorization |
| **Celery Worker** | Prod | 2 / 4 | 4Gi / 8Gi | KEDA/HPA: Scales based on Redis Queue depth |
| **PostgreSQL** | Prod | 2 / 4 | 8Gi / 16Gi | Tuned for `shared_buffers` = 4GB |
| **Qdrant** | Prod | 2 / 8 | 8Gi / 32Gi | Extremely memory intensive for large dense vectors |
| **vLLM (GPU)** | Prod | 8 / 16 | 32Gi / 64Gi | **Crucial:** Needs 1-4 NVIDIA GPUs (A100/H100) depending on model parameters and quantization. |

> **Warning:** vLLM requires exact GPU NodeSelectors (`accelerator: nvidia-gpu`) and tolerations to schedule properly. Do not run LLMs on CPU nodes in production; latency will be unacceptable.
