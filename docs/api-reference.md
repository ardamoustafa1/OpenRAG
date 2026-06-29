# API Reference

The Enterprise RAG Platform offers a robust REST API for integrating with custom applications without using our frontend UI.

## Authentication

All API endpoints (except `/auth/*`) require a Bearer token or API Key. Additionally, the `X-Tenant-ID` header must be provided to enforce tenant isolation.

```http
Authorization: Bearer <your_token>
X-Tenant-ID: <your_tenant_uuid>
```

---

## Endpoints

### Authentication

#### `POST /api/v1/auth/login`
Authenticate with email and password to receive JWT tokens.
- **Body:** `{ "email": "user@example.com", "password": "password123" }`
- **Response:** `{ "access_token": "...", "refresh_token": "..." }`

#### `POST /api/v1/auth/refresh`
Rotate access token using a valid refresh token.
- **Body:** `{ "refresh_token": "..." }`
- **Response:** `{ "access_token": "...", "refresh_token": "..." }`

---

### Chat & Generation

#### `POST /api/v1/conversations/{id}/messages`
Send a message and receive a Server-Sent Events (SSE) stream.
- **Body:** 
  ```json
  {
    "content": "What is the remote work policy?",
    "collection_id": "uuid-here"
  }
  ```
- **Response (Stream):**
  ```text
  data: {"id": "msg-123", "content": "According to the policy", "role": "assistant"}
  ...
  ```

---

### Documents & Ingestion

#### `POST /api/v1/collections`
Create a new document collection.
- **Body:** `{ "name": "HR Docs", "description": "Internal HR" }`
- **Response:** `{ "id": "...", "name": "HR Docs" }`

#### `POST /api/v1/collections/{id}/documents/upload`
Upload a document for processing.
- **Content-Type:** `multipart/form-data`
- **Form Data:** `file` (Binary file data)
- **Response:** `{ "message": "Document uploaded and processing started", "document_id": "..." }`

---

### API Keys

#### `POST /api/v1/api-keys`
Generate a long-lived API key for service accounts.
- **Body:** `{ "name": "CI Bot", "permissions": ["chat", "read"] }`
- **Response:** `{ "id": "...", "raw_key": "sk-123..." }` (Raw key is only shown once).
