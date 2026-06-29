import uuid
from typing import Callable
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.db import async_session_factory
from app.models.log import AuditLog
import structlog

logger = structlog.get_logger()

async def log_audit_event_async(action: str, resource_type: str, user_id: uuid.UUID | None, tenant_id: uuid.UUID | None, ip_address: str | None, user_agent: str | None):
    async with async_session_factory() as db:
        try:
            log_entry = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=uuid.uuid4(),  # Generic ID for middleware-level logging
                user_id=user_id,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(log_entry)
            await db.commit()
        except Exception as e:
            logger.error("Failed to write audit log", error=str(e))

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add standard security headers to every response.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract the tenant ID from a custom header (e.g., X-Tenant-ID)
    or from the host/subdomain.
    We set it in request.state so dependencies can easily read it.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = request.headers.get("X-Tenant-ID")
        # Alternative: extract from host like request.client.host
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response

class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log high-level API access events to the audit_logs table async.
    In a real-world scenario, this might be handled via a background task or message queue
    to avoid delaying the HTTP response, but for demonstration, we'll log it directly if applicable.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # We extract user_id and tenant_id from request.state
            user_id = getattr(request.state, "user_id", None)
            tenant_id = getattr(request.state, "tenant_id", None)
            
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            # Fire-and-forget background task to write audit log without delaying response
            asyncio.create_task(
                log_audit_event_async(
                    action=request.method,
                    resource_type=request.url.path[:100],  # Truncate to match DB schema
                    user_id=user_id,
                    tenant_id=tenant_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            )
        return response
