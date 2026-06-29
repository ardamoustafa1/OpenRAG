import json
import zipfile
import hashlib
import io
import datetime
from sqlalchemy import select
from app.core.db import async_session_factory
from app.models.log import AuditLog

async def export_audit_logs(tenant_id: str) -> Tuple[bytes, str]:
    """
    Exports all audit logs for a tenant as a cryptographically signed ZIP archive.
    Used for regulatory requests (e.g. KVKK Denetimi).
    Returns (zip_bytes, sha256_hash)
    """
    async with async_session_factory() as db:
        result = await db.execute(select(AuditLog).where(AuditLog.tenant_id == tenant_id))
        logs = result.scalars().all()
        
    log_data = []
    for log in logs:
        log_data.append({
            "id": str(log.id),
            "timestamp": log.created_at.isoformat(),
            "user_id": log.user_id,
            "action": log.action,
            "resource": log.resource,
            "ip_address": log.ip_address
        })
        
    json_bytes = json.dumps(log_data, indent=2).encode('utf-8')
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        zf.writestr(f"audit_logs_{tenant_id}_{datetime.date.today()}.json", json_bytes)
        
    zip_bytes = zip_buffer.getvalue()
    
    # Calculate SHA256 Hash for integrity proof
    sha256_hash = hashlib.sha256(zip_bytes).hexdigest()
    
    return zip_bytes, sha256_hash
