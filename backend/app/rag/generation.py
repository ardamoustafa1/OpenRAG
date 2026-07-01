import json
from typing import Any, AsyncGenerator

import structlog

from app.llm.client import llm_client
from app.rag.prompt_manager import prompt_manager

logger = structlog.get_logger()

PLATFORM_BASE_PROMPT = """
You are a secure Enterprise AI Assistant.
Rules:
1. ONLY answer using the provided context.
2. If the context does not contain the answer, say exactly: "I could not find information on this topic in my documents." Do NOT use outside knowledge.
3. For every claim you make, you MUST cite the source inline like this: [Source: Document Name, Section: Section].
4. Interpret the context to help the user, but NEVER hallucinate or invent information.
"""


class GenerationService:
    """
    Handles prompt construction and SSE streaming for chat responses.
    """

    def build_system_prompt(self, tenant_settings: dict[str, Any]) -> str:
        tenant_prompt = tenant_settings.get("system_prompt", "")
        return prompt_manager.build_system_prompt(PLATFORM_BASE_PROMPT, tenant_prompt)

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        context_string: str,
        tenant_settings: dict[str, Any],
        tenant_id: str,
        sources: list[dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """
        Generates Server-Sent Events (SSE) stream.
        Yields JSON strings formatted as SSE data.
        """
        # 1. Prepare system prompt
        system_content = self.build_system_prompt(tenant_settings)
        if context_string:
            system_content += f"\n\nCONTEXT:\n{context_string}"

        # 2. Inject system prompt at the beginning
        final_messages = [{"role": "system", "content": system_content}] + messages

        # 3. Stream from LLM
        try:
            generator = llm_client.astream_chat(
                model=model, messages=final_messages, tenant_id=tenant_id
            )

            async for chunk_text in generator:
                payload = {"type": "token", "content": chunk_text}
                yield f"data: {json.dumps(payload)}\n\n"

            # 4. Stream sources at the end
            sources_payload = {"type": "sources", "sources": sources}
            yield f"data: {json.dumps(sources_payload)}\n\n"

            # 5. Done marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error("Error during SSE stream generation", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'content': 'Generation failed.'})}\n\n"
            yield "data: [DONE]\n\n"


generation_service = GenerationService()
