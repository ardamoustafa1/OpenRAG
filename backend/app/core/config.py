from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal

class Settings(BaseSettings):
    """
    Application Settings.
    These are read from the environment variables, prioritizing a `.env` file if present.
    """

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Current execution environment"
    )
    LOG_LEVEL: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
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
    MINIO_ACCESS_KEY: str = Field(
        default="admin", description="MinIO access key"
    )
    MINIO_SECRET_KEY: str = Field(
        default="admin123", description="MinIO secret key"
    )
    MINIO_SECURE: bool = Field(
        default=False, description="Set to True if MinIO is served over HTTPS"
    )

    # LLM Services
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434", description="Base URL for local Ollama instance"
    )
    LITELLM_BASE_URL: str | None = Field(
        default=None, description="Optional Base URL for LiteLLM proxy"
    )

    # Security & Auth
    SECRET_KEY: str = Field(
        ..., # Required field
        description="Secret key for JWT token signing"
    )
    ALGORITHM: str = Field(
        default="HS256", description="Algorithm used to sign JWTs"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="Access token expiration time in minutes (default 60 min)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration time in days"
    )

    # CORS
    CORS_ALLOW_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins. In production, set explicitly to your domain(s)."
    )
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1", "api.localhost", "app.localhost"],
        description="Allowed hosts for TrustedHostMiddleware"
    )

    # Billing (Stripe)
    STRIPE_API_KEY: str | None = Field(
        default=None, description="Stripe API secret key for billing"
    )
    STRIPE_WEBHOOK_SECRET: str | None = Field(
        default=None, description="Stripe webhook endpoint secret for signature verification"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Ignore extra env vars
    )

# Create a global instance of settings
settings = Settings()
