from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings.
    These are read from the environment variables, prioritizing a `.env` file if present.
    """

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Current execution environment"
    )
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix string")
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Database (PostgreSQL)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db",
        description="PostgreSQL Connection URL (using asyncpg)",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis Connection URL for Celery broker and caching",
    )

    # Vector Database (Qdrant)
    QDRANT_HOST: str = Field(
        default="localhost", description="Host where Qdrant is running"
    )
    QDRANT_PORT: int = Field(
        default=6333, description="Port where Qdrant is accessible via REST API"
    )

    # Object Storage (MinIO)
    MINIO_ENDPOINT: str = Field(
        default="localhost:9000", description="MinIO endpoint without scheme"
    )
    MINIO_ACCESS_KEY: str = Field(default="admin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="admin123", description="MinIO secret key")
    MINIO_SECURE: bool = Field(
        default=False, description="Set to True if MinIO is served over HTTPS"
    )
    MINIO_BUCKET_NAME: str = Field(
        default="documents", description="Default MinIO bucket for uploaded documents"
    )

    # LLM Services
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama instance",
    )
    LITELLM_BASE_URL: str | None = Field(
        default=None, description="Optional Base URL for LiteLLM proxy"
    )

    # Security & Auth
    SECRET_KEY: str = Field(
        ..., description="Secret key for JWT token signing"  # Required field
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used to sign JWTs (use RS256 in prod with RSA keys)",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Access token expiration time in minutes (default 60 min)",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration time in days"
    )

    # CORS
    CORS_ALLOW_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins. In production, set explicitly to your domain(s).",
    )
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1", "api.localhost", "app.localhost"],
        description="Allowed hosts for TrustedHostMiddleware",
    )

    # Frontend URL (used in email links)
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Base URL of the frontend application (used in email reset links)",
    )

    # Email / SMTP
    SMTP_HOST: str = Field(
        default="",
        description="SMTP server hostname (e.g., smtp.sendgrid.net). Leave empty to use dev logging mode.",
    )
    SMTP_PORT: int = Field(
        default=587, description="SMTP server port (587 for STARTTLS, 465 for SSL)"
    )
    SMTP_USER: str = Field(
        default="", description="SMTP authentication username or API key"
    )
    SMTP_PASSWORD: str = Field(
        default="", description="SMTP authentication password or API key value"
    )
    EMAIL_FROM_ADDRESS: str = Field(
        default="noreply@openrag.com", description="From address for outbound emails"
    )
    EMAIL_FROM_NAME: str = Field(
        default="OpenRAG", description="From display name for outbound emails"
    )

    # Billing (Stripe)
    STRIPE_API_KEY: str | None = Field(
        default=None, description="Stripe API secret key for billing"
    )
    STRIPE_WEBHOOK_SECRET: str | None = Field(
        default=None,
        description="Stripe webhook endpoint secret for signature verification",
    )

    # Observability (Langfuse)
    LANGFUSE_PUBLIC_KEY: str | None = Field(
        default=None, description="Langfuse Public Key for tracing"
    )
    LANGFUSE_SECRET_KEY: str | None = Field(
        default=None, description="Langfuse Secret Key for tracing"
    )
    LANGFUSE_HOST: str = Field(
        default="http://localhost:3000", description="Langfuse Host URL"
    )
    OTLP_ENDPOINT: str | None = Field(
        default=None,
        description="OpenTelemetry Collector Endpoint (e.g., http://otel-collector:4317)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars
    )

    @model_validator(mode="after")
    def validate_prod_algorithm(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.ALGORITHM == "HS256":
            raise ValueError(
                "HS256 algorithm is not secure enough for production. Please configure RS256 with RSA keys."
            )
        return self


# Create a global instance of settings
settings = Settings()  # type: ignore[call-arg]
