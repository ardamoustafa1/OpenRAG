import asyncio
import json
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.db import get_db_session
from app.core.dependencies import get_current_tenant, get_current_user
from app.core.rate_limit import limiter
from app.llm.token_counter import token_counter
from app.models.chat import Conversation, Message
from app.models.tenant import Tenant
from app.models.user import User
from app.rag.citation import citation_service
from app.rag.context_builder import context_builder
from app.rag.generation import generation_service
from app.rag.reranking import reranker
from app.rag.retrieval import retriever

logger = structlog.get_logger()


class SendMessageRequest(BaseModel):
    content: str
    collection_id: str


# Imports moved to top

router = APIRouter(tags=["Chat"])


@router.post("/conversations")
async def create_conversation(
    title: str = "New Conversation",
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
):
    conv = Conversation(tenant_id=tenant.id, user_id=user.id, title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.post("/conversations/{conversation_id}/messages")
@limiter.limit("20/minute")
async def send_message(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
):
    """
    Sends a message to a conversation and streams the SSE response.
    Includes full RAG pipeline execution.
    """
    # 1. Verify Conversation
    stmt = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.tenant_id == tenant.id
    )
    conv = (await db.execute(stmt)).scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Save User Message
    user_msg = Message(conversation_id=conv.id, role="user", content=payload.content)
    db.add(user_msg)
    await db.commit()

    # 3. Retrieve Chat History
    stmt = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    history = (await db.execute(stmt)).scalars().all()

    messages = [{"role": m.role, "content": m.content} for m in history]

    # 4. Truncate context if too long
    messages = token_counter.truncate_context(messages, max_tokens=3000)

    async def sse_generator():
        # Pipeline execution inside the generator
        try:
            # A. Retrieve
            retrieved = await retriever.retrieve(
                query=payload.content,
                tenant_id=str(tenant.id),
                collection_id=payload.collection_id,
            )

            # B. Re-rank
            reranked = reranker.rerank(
                query=payload.content, retrieved_chunks=retrieved, top_k=10
            )

            # C. Context Build
            used_chunks, context_str = context_builder.build_context(
                reranked, max_context_tokens=4000
            )

            # D. Format Sources
            sources = citation_service.format_sources(used_chunks)

            # E. Stream Generation
            model_to_use = tenant.settings.get("default_model", "qwen2.5-72b")

            # Accumulate tokens for DB persistence after stream completes
            full_response = ""

            generator = generation_service.stream_chat(
                model=model_to_use,
                messages=messages,
                context_string=context_str,
                tenant_settings=tenant.settings,
                tenant_id=str(tenant.id),
                sources=sources,
            )

            async for chunk in generator:
                yield chunk

                if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                    try:
                        data_json = json.loads(chunk[6:].strip())
                        if data_json.get("type") == "token":
                            full_response += data_json.get("content", "")
                    except Exception:
                        pass

            # Save assistant response to DB in a new session
            if full_response:
                from app.core.db import async_session_factory

                async with async_session_factory() as local_db:
                    assistant_msg = Message(
                        conversation_id=conv.id, role="assistant", content=full_response
                    )
                    local_db.add(assistant_msg)
                    await local_db.commit()

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return EventSourceResponse(sse_generator())


@router.post("/chat/quick")
async def quick_chat(
    payload: SendMessageRequest,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
):
    """Stateless chat completion without saving to DB."""

    async def sse_generator():
        retrieved = await retriever.retrieve(
            query=payload.content,
            tenant_id=str(tenant.id),
            collection_id=payload.collection_id,
        )
        reranked = reranker.rerank(
            query=payload.content, retrieved_chunks=retrieved, top_k=10
        )
        used_chunks, context_str = context_builder.build_context(
            reranked, max_context_tokens=4000
        )
        sources = citation_service.format_sources(used_chunks)

        generator = generation_service.stream_chat(
            model=tenant.settings.get("default_model", "qwen2.5-72b"),
            messages=[{"role": "user", "content": payload.content}],
            context_string=context_str,
            tenant_settings=tenant.settings,
            tenant_id=str(tenant.id),
            sources=sources,
        )

        async for chunk in generator:
            yield chunk

    return EventSourceResponse(sse_generator())
