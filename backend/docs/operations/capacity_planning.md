# Capacity Planning Guide

The following formulas predict the hardware boundaries of the Enterprise AI Platform. Buffer limits account for load spikes.

## Formulas

- **CPU Cores:** `(Concurrent_Users * Avg_Response_CPU) + (Daily_Docs * Processing_CPU) + 30% Buffer`
- **RAM:** `(Model_Size * 1.2) + Context_Cache + OS_Overhead + 20% Buffer`
- **Disk Space:** `(Avg_Doc_Size * Daily_Docs * Retention_Days) + (PostgreSQL_Growth) + (Backup_Space * 2)`
- **GPU VRAM:** `(Model_Weights_FP16_Size) + (KV_Cache * Concurrent_Requests) + 10% Buffer`

## Deployment Tier Profiles

### 1. Starter Tier
- **Workload:** 50 Users, 1,000 Documents. Small context windows.
- **Backend Nodes:** 2x Nodes (4 Cores, 8GB RAM).
- **GPU Node:** 1x NVIDIA L4 or A10G (24GB VRAM) for lightweight quantization models (e.g., `phi-4-mini` or `llama-3-8b`).
- **Disk:** 500GB SSD.

### 2. Professional Tier
- **Workload:** 500 Users, 50,000 Documents. Deep retrieval.
- **Backend Nodes:** 3x Nodes (8 Cores, 16GB RAM).
- **Celery Workers:** 2x Nodes (8 Cores, 16GB RAM) dedicated to ingestion.
- **GPU Node:** 1x NVIDIA A100 (80GB VRAM) or 2x A100 (40GB) running `llama3.3-70b` (quantized) or `qwen2.5-72b`.
- **Disk:** 2TB NVMe.

### 3. Enterprise Tier
- **Workload:** 5,000+ Users, >1 Million Documents. Air-gapped, high concurrency.
- **Backend Nodes:** 5-10x Nodes (16 Cores, 32GB RAM) managed by HPA.
- **Database Nodes:** Dedicated Postgres Cluster (32 Cores, 128GB RAM).
- **GPU Nodes:** 4x NVIDIA A100 (80GB VRAM) or H100 with Tensor Parallelism spanning multiple GPUs.
- **Disk:** 10TB+ NVMe with specialized ReadWriteMany (RWX) storage arrays.
