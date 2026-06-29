# Cloud Cost Optimization Strategies

Running large language models and massive vector databases scales costs aggressively. Apply these strategies to reduce monthly cloud expenditure.

## 1. GPU Compute Reduction
- **Quantization:** Do not run raw `fp16` models unless absolutely necessary. Using `AWQ` or `GPTQ` quantized models via vLLM can reduce VRAM requirements by 50-60%, allowing you to use cheaper GPUs (e.g., L4 instead of A100).
- **Model Fallbacks:** Route generic/simple queries to a lightweight model (e.g., `phi-4-mini` or `llama-3-8b`) running on smaller nodes. Only invoke the massive 70B+ models for deep reasoning or complex code questions.
- **Semantic Caching:** Store previous identical or highly similar RAG queries in Redis. If a semantic match is >95%, return the cached response instantly without invoking the GPU.

## 2. Infrastructure & Storage
- **Celery Spot Instances:** Document ingestion (PDF OCR, chunking) is an asynchronous background task. Run Celery workers on cloud **Spot / Preemptible Instances**. If a worker is interrupted, the message remains in Redis and is picked up by another worker. Saves up to 70% on CPU compute.
- **Vector Database Compaction:** Regularly run Qdrant payload optimization.
- **Cold Storage:** Compress (zstd/gzip) and move unused or archived tenant documents to MinIO Cold tiers / AWS S3 Glacier to save block storage costs.

## 3. Elasticity
- Utilize Kubernetes **HorizontalPodAutoscaler (HPA)** for the Frontend and API Backend. Scale down to 2 replicas at night and scale up to 20 during business hours based on CPU load.
