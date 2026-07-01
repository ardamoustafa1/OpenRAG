from prometheus_client import Counter, Gauge, Histogram

# LLM Latency Histogram
llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "Duration of LLM requests in seconds",
    labelnames=["model", "tenant_id"],
)

# Token Counters
llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total number of tokens processed",
    labelnames=["model", "tenant_id", "type"],  # type = prompt or completion
)

# Error Counters
llm_errors_total = Counter(
    "llm_errors_total", "Total number of LLM errors", labelnames=["model", "error_type"]
)

# Queue Depth Gauge
llm_queue_depth = Gauge(
    "llm_queue_depth",
    "Current number of pending LLM requests in the queue",
    labelnames=["model"],
)

# GPU Memory Gauge (Pseudo implementation - requires external exporter for real data)
gpu_memory_used_bytes = Gauge(
    "gpu_memory_used_bytes", "GPU memory currently used in bytes", labelnames=["device"]
)
