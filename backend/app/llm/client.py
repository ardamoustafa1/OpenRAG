from typing import Any, AsyncGenerator

import litellm
import structlog
from litellm import acompletion, aembedding

logger = structlog.get_logger()

# By connecting via LiteLLM proxy, we actually use the LiteLLM proxy URL
# as our base URL, and send standard OpenAI-formatted requests to it.
LITELLM_PROXY_URL = "http://litellm:4000"

# Note: Alternatively, we can use the LiteLLM python package directly as a router
# But since we have a dedicated litellm proxy container, we should communicate with it via httpx/OpenAI client,
# or set litellm.api_base to our proxy. We'll use the litellm package for convenience to wrap calls to the proxy.
litellm.api_base = LITELLM_PROXY_URL
litellm.api_key = (
    "sk-placeholder"  # Proxy might not need auth internally if we secure the network
)


class LLMClient:
    """
    Wrapper around LiteLLM to interact with the LLM Orchestration Proxy.
    Handles streaming, standard chats, and embeddings, injecting observability headers.
    """

    async def astream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tenant_id: str,
        user_id: str | None = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses. Injects Langfuse metadata."""
        metadata = {"tenant_id": tenant_id, "user_id": user_id}

        try:
            response = await acompletion(
                model=model, messages=messages, stream=True, metadata=metadata, **kwargs
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("LLM Streaming failed", error=str(e), model=model)
            raise

    async def achat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tenant_id: str,
        user_id: str | None = None,
        **kwargs: Any
    ) -> Any:
        """Standard chat completion request."""
        metadata = {"tenant_id": tenant_id, "user_id": user_id}
        try:
            response = await acompletion(
                model=model, messages=messages, metadata=metadata, **kwargs
            )
            return response
        except Exception as e:
            logger.error("LLM Chat failed", error=str(e), model=model)
            raise

    async def aembed(self, model: str, input_text: str, tenant_id: str) -> list[float]:
        """Generate embedding for a single string."""
        metadata = {"tenant_id": tenant_id}
        try:
            response = await aembedding(
                model=model, input=input_text, metadata=metadata
            )
            return response.data[0]["embedding"]  # type: ignore[no-any-return]
        except Exception as e:
            logger.error("LLM Embedding failed", error=str(e), model=model)
            raise

    async def aembed_batch(
        self, model: str, input_texts: list[str], tenant_id: str
    ) -> list[list[float]]:
        """Generate embeddings for a list of strings."""
        metadata = {"tenant_id": tenant_id}
        try:
            response = await aembedding(
                model=model, input=input_texts, metadata=metadata
            )
            return [data["embedding"] for data in response.data]
        except Exception as e:
            logger.error("LLM Batch Embedding failed", error=str(e), model=model)
            raise

    async def alist_models(self) -> list[dict[str, Any]]:
        """List available models from the proxy (pseudo-implementation)."""
        # Typically, you'd GET /v1/models from the proxy via httpx
        return [{"id": "llama3.3-70b"}, {"id": "qwen2.5-72b"}, {"id": "phi-4-mini"}]


llm_client = LLMClient()
