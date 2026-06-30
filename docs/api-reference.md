# Complete API Reference

The Enterprise RAG Platform operates purely on a headless REST architecture. Everything possible in the UI can be performed via this API.

## Base URL
All API paths are relative to `https://api.yourdomain.com/api/v1`

## Authentication & Multi-Tenancy

Every request (except `/auth/login`) requires two headers:

```http
Authorization: Bearer <JWT_ACCESS_TOKEN or API_KEY>
X-Tenant-ID: <UUID>
```

---

## 1. Authentication Router (`/auth`)

### `POST /auth/login`
Authenticate a user and return an access token.
- **Request Body:** `{ "email": "user@example.com", "password": "password123" }`
- **Response:** `200 OK`
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "mfa_required": false
  }
  ```

### `GET /auth/me`
Fetch the currently authenticated user's profile.
- **Response:** `200 OK`
  ```json
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Jane Doe",
    "role": "tenant_admin"
  }
  ```

---

## 2. Collections Router (`/collections`)

Collections are isolated silos of documents. A chat session is always scoped to a single collection.

### `POST /collections`
- **Request Body:** `{ "name": "HR Handbooks", "description": "Policies for 2026" }`
- **Response:** `201 Created`

### `GET /collections`
List all collections accessible to the current tenant.
- **Response:** `200 OK` (Array of collections).

---

## 3. Documents Router (`/documents`)

### `POST /documents`
Upload a document to a collection. The document is asynchronously chunked and embedded by Celery workers.
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: (Binary File)
  - `collection_id`: `uuid`
- **Response:** `202 Accepted`
  ```json
  {
    "document_id": "uuid",
    "status": "processing"
  }
  ```

### `GET /documents/{document_id}`
Check the ingestion status (`processing`, `completed`, `failed`).

---

## 4. Chat Router (`/chat`)

### `POST /chat/completions`
Send a message and receive a streaming response containing the generated answer and the source chunks used (citations).
- **Request Body:**
  ```json
  {
    "messages": [{"role": "user", "content": "What is our WFH policy?"}],
    "collection_id": "uuid",
    "stream": true
  }
  ```
- **Response:** `200 OK (text/event-stream)`
  ```text
  data: {"content": "Our WFH policy allows "}
  data: {"content": "2 days remote.", "citations": [{"doc_id": "uuid", "page": 4}]}
  ```

---

## 5. API Keys Router (`/api-keys`)

Manage service accounts for automated integrations.

### `POST /api-keys`
- **Request Body:** `{ "name": "SlackBot Sync", "scopes": ["read", "chat"] }`
- **Response:** `201 Created`
  ```json
  {
    "key_id": "uuid",
    "raw_key": "sk-abc123def456..." 
  }
  ```
  *(Note: `raw_key` is only returned once and hashed immediately).*

---

## 6. Admin Router (`/admin`)

Requires `super_admin` role. Used for global platform administration.

### `GET /admin/users`
List all users across all tenants.

### `POST /admin/tenants`
Provision a new tenant and initialize their dedicated Postgres schema and Qdrant index.

---

## 7. Billing Router (`/billing`)

Manage Stripe subscriptions and quota allocations.

### `POST /billing/portal`
Generates a Stripe Customer Portal session URL.
- **Response:** `{ "url": "https://billing.stripe.com/p/session/..." }`

### `POST /billing/webhook`
Receives Stripe asynchronous events (`invoice.paid`, `customer.subscription.deleted`).

---

## 8. Quota Router (`/quota`)

View current tenant usage.

### `GET /quota/usage`
- **Response:** `200 OK`
  ```json
  {
    "tokens_used_this_month": 1504200,
    "documents_indexed": 420,
    "storage_bytes": 104857600
  }
  ```

---

## 9. Webhooks Router (`/webhooks`)

Subscribe to async platform events (e.g., get a ping when a 1000-page PDF finishes embedding).

### `POST /webhooks`
- **Request Body:**
  ```json
  {
    "endpoint": "https://your-internal-app.com/callback",
    "events": ["document.ingested", "document.failed"]
  }
  ```
- **Response:** `201 Created`
