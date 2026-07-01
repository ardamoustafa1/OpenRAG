from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_tenant_id_or_ip(request: Request) -> str:
    """
    Extracts tenant_id from request state (set by TenantMiddleware).
    Falls back to IP address if tenant_id is missing (e.g., unauthenticated routes).
    """
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return str(request.state.tenant_id)
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(key_func=get_tenant_id_or_ip, default_limits=["1000/minute"])
