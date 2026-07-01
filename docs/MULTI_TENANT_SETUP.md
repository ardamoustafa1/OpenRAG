# 🏢 Multi-Tenant Setup & Architecture

OpenRAG is built from the ground up for true B2B multi-tenancy. A "Tenant" represents an isolated workspace — this could be a different company using your SaaS, or a different department within your enterprise (e.g., HR, Engineering, Legal).

## 🔒 The Three Layers of Isolation

Data never crosses tenant boundaries. We enforce this at three levels:

1. **API / Middleware Layer (`TenantMiddleware`)**:
   Every incoming HTTP request requires an `X-Tenant-ID` header (or it's extracted from the JWT token). This ID is bound to a thread-local context variable for the duration of the request.

2. **Database Layer (Row-Level Security)**:
   All tables in PostgreSQL include a `tenant_id` column. We use SQLAlchemy global filters to ensure that `SELECT`, `UPDATE`, and `DELETE` queries automatically append `WHERE tenant_id = :current_tenant_id`.

3. **Vector Database Layer (Qdrant)**:
   Qdrant doesn't natively support "databases" like Postgres. Instead, every single vector payload contains a `tenant_id` field. The retrieval engine forcibly injects a `Must(tenant_id == X)` filter into every semantic search.

## 🛠️ Configuring a New Tenant

### 1. Via the Admin UI
1. Log in as a Super Admin at `http://localhost:3000/admin`.
2. Click **Tenants** > **Add New Tenant**.
3. Provide a Name and define resource quotas (Max Users, Max Storage, Max Documents).
4. The system will automatically provision the underlying storage buckets in MinIO.

### 2. Via the Python SDK
```python
from openrag import AIPlatformClient

client = AIPlatformClient(api_key="super_admin_key", tenant_url="http://api.localhost")

# Create a new tenant
new_tenant = client.create_tenant(
    name="Acme Corp",
    plan="enterprise",
    quotas={"max_docs": 5000}
)

print(f"Created tenant ID: {new_tenant.id}")
```

## 👥 User Roles within a Tenant

Users belong to a specific tenant and have one of three roles:
- **Tenant Admin**: Can add users, configure tenant-specific LLMs, and view billing usage.
- **Editor**: Can upload and delete documents, create collections, and chat.
- **Viewer**: Can only chat with existing collections.

## 🌐 White-Labeling (Custom Domains)

OpenRAG supports routing based on domains. If a user visits `acme.your-saas.com`, the Next.js frontend will automatically inject the `Acme Corp` tenant ID into API requests.

Configure this in the frontend `.env`:
```env
NEXT_PUBLIC_ENABLE_SUBDOMAIN_ROUTING=true
NEXT_PUBLIC_ROOT_DOMAIN=your-saas.com
```
