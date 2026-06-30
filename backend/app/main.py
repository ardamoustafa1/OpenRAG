"""
Enterprise RAG AI Platform - Main Entrypoint
============================================

This module initializes the FastAPI application, configuring all core services,
middlewares, and observability tools required for a production-grade, 
on-premise RAG system.

Key Features Bootstrapped Here:
1. **OpenTelemetry Tracing**: Distributed tracing exported via OTLP.
2. **Prometheus Metrics**: Automatic metrics exposed at `/metrics`.
3. **Structured Logging**: Contextual, JSON-formatted logs via structlog.
4. **Middlewares**: Security headers, CORS, Tenant isolation, Audit logging.
5. **Rate Limiting**: IP-based rate limiting via SlowAPI.
"""

import uuid
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

# Prometheus and rate limiting
from prometheus_client import make_asgi_app
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# OpenTelemetry Tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# local imports
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.middleware import SecurityHeadersMiddleware, TenantMiddleware, AuditMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.admin import router as admin_router
from app.api.v1.billing import router as billing_router
from app.api.health import router as health_router

# Setup structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        structlog.stdlib.INFO if settings.LOG_LEVEL == "INFO" else structlog.stdlib.DEBUG
    ),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle events of the FastAPI application.
    - Startup: Initializes necessary external connections.
    - Shutdown: Gracefully closes database and Redis connections.
    """
    logger.info("Starting up Enterprise RAG Platform...")
    yield
    logger.info("Shutting down Enterprise RAG Platform...")
    
    try:
        from app.db.session import engine
        logger.info("Disposing SQLAlchemy Engine...")
        await engine.dispose()
        logger.info("SQLAlchemy Engine disposed cleanly.")
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")

# Initialize FastAPI App
# Note: OpenAPI docs are automatically disabled in production for security.
app = FastAPI(
    title="Enterprise RAG AI Platform",
    description="A highly secure, multi-tenant, 100% on-premise RAG platform API.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None
)

# OpenTelemetry Setup
resource = Resource.create({"service.name": "OpenRAG-api", "service.version": "0.1.0"})
trace.set_tracer_provider(TracerProvider(resource=resource))
# Note: In production, the OTLP_ENDPOINT would be fetched from settings (e.g., http://otel-collector:4317)
otlp_exporter = OTLPSpanExporter() 
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
FastAPIInstrumentor.instrument_app(app)

# --- Middlewares ---

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# Tenant & Audit
app.add_middleware(AuditMiddleware)
app.add_middleware(TenantMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Tenant-ID",
        "Accept",
        "Accept-Encoding",
        "Accept-Language",
    ],
)

# Rate Limiting Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Request ID & Structured Logging Middleware
@app.middleware("http")
async def structlog_request_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    
    start_time = time.perf_counter()
    logger.info("Request started")
    
    try:
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        logger.info("Request completed", status_code=response.status_code, duration=process_time)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        process_time = time.perf_counter() - start_time
        logger.exception("Request failed", duration=process_time, error=str(exc))
        raise

# --- Global Exception Handlers ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": structlog.contextvars.get_contextvars().get("request_id", "unknown")
        }
    )

# Mount Prometheus Metrics Endpoint (single mount)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- Health Endpoint ---
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

# --- Routers ---
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(api_keys_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(health_router)
