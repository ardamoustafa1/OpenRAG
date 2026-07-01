from prometheus_client import Counter, Gauge, Histogram

# --- API Metrics ---
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status", "tenant_id"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "tenant_id"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)

# --- LLM Metrics ---
llm_requests_total = Counter(
    "llm_requests_total", "Total LLM requests", ["model", "tenant_id", "status"]
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["model", "tenant_id", "type"],  # token category: prompt or completion
)

llm_latency_seconds = Histogram(
    "llm_latency_seconds", "LLM response latency", ["model", "tenant_id"]
)

llm_cache_hits_total = Counter(
    "llm_cache_hits_total", "Total semantic cache hits", ["tenant_id"]
)

# --- RAG Metrics ---
rag_retrieval_duration = Histogram(
    "rag_retrieval_duration_seconds", "Time spent in hybrid retrieval", ["tenant_id"]
)

rag_rerank_duration = Histogram(
    "rag_rerank_duration_seconds",
    "Time spent in cross-encoder reranking",
    ["tenant_id"],
)

rag_no_answer_total = Counter(
    "rag_no_answer_total",
    "Number of times RAG could not find an answer in context",
    ["tenant_id"],
)

rag_avg_retrieval_score = Gauge(
    "rag_avg_retrieval_score",
    "Average top-1 RRF or Rerank score per query",
    ["tenant_id"],
)

# --- Document Metrics ---
documents_processed_total = Counter(
    "documents_processed_total",
    "Total documents processed by ingestion pipeline",
    ["tenant_id", "status"],
)

document_processing_duration = Histogram(
    "document_processing_duration_seconds", "Document ingestion duration", ["tenant_id"]
)

document_chunks_total = Gauge(
    "document_chunks_total", "Total chunks indexed", ["tenant_id"]
)

# --- System Metrics ---
active_conversations = Gauge(
    "active_conversations_total", "Active chat sessions", ["tenant_id"]
)

celery_queue_depth = Gauge(
    "celery_queue_depth", "Number of tasks waiting in Celery queues", ["queue_name"]
)

gpu_memory_used_bytes = Gauge(
    "gpu_memory_used_bytes", "GPU memory allocated", ["device"]
)

gpu_utilization_percent = Gauge(
    "gpu_utilization_percent", "GPU compute utilization", ["device"]
)
