# Performance Test Report

**Date of Execution:** `YYYY-MM-DD`
**Target Environment:** `Staging | Production`
**Version/Commit:** `[SHA]`

## 1. Chat API Load Test (`locustfile_chat.py`)
- **Concurrent Users:** 100
- **Duration:** 10 minutes
- **Requests per Second (RPS):** ______

### Latency Metrics
- **Median:** ______ ms
- **Average:** ______ ms
- **p95:** ______ ms (Target: < 10,000 ms)
- **p99:** ______ ms
- **Error Rate:** ______ % (Target: < 1%)

## 2. Ingestion Pipeline Load Test (`locustfile_ingestion.py`)
- **Concurrent Uploads:** 20 documents (10MB each)
- **Celery Max Queue Depth:** ______ tasks
- **Average Processing Time per Doc:** ______ seconds

## 3. Bottleneck Analysis & Notes
- *Observe any OOMKilled pods, Redis spikes, or Qdrant CPU throttling.*
- *Insert Grafana screenshots here.*
