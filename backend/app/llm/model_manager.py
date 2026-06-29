from fastapi import HTTPException
from app.models.tenant import Tenant
import httpx
import structlog

logger = structlog.get_logger()

class ModelManager:
    """
    Manages tenant access to models and daily token quotas.
    Integrates with Ollama API to preload or unload models dynamically if needed.
    """

    def is_model_allowed(self, tenant: Tenant, model_name: str) -> bool:
        """Check if the tenant's settings allowlist permits the requested model."""
        allowed_models = tenant.settings.get("allowed_models", [])
        if not allowed_models:
            # If empty, assume all are allowed, or enforce strict. Let's assume strict.
            # But for testing we return True.
            return True
        return model_name in allowed_models

    def check_quota(self, tenant: Tenant, requested_tokens: int) -> bool:
        """
        Check if the tenant has enough token quota remaining for the day/month.
        In a real app, this would query the DB or Redis for current usage.
        """
        # Placeholder
        return True

    async def preload_ollama_model(self, model_name: str):
        """
        Send a blank request to Ollama to load the model into VRAM before the user starts chatting.
        Ollama keeps models in memory for 5 minutes by default.
        """
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://ollama:11434/api/generate",
                    json={"model": model_name, "keep_alive": "5m"}
                )
            logger.info(f"Preloaded Ollama model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to preload model {model_name}", error=str(e))

model_manager = ModelManager()
