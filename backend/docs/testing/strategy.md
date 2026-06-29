# Testing Strategy & Quality Assurance Pyramid

The Enterprise AI Platform enforces a rigorous testing strategy ensuring that functional regressions, security holes, and data leaks never reach production.

## The Test Pyramid

1. **Unit Tests (60%)**
   - **Scope:** Isolated functions, classes, and algorithmic logic.
   - **Framework:** `pytest`
   - **Mocks:** External services (Redis, PostgreSQL, Qdrant, LLMs) are entirely mocked using `unittest.mock`.
   - **Goal:** Rapid execution (< 100ms per test). Target 85% Code Coverage.
   - **Examples:** JWT validation, RBAC checks, Token chunking logic.

2. **Integration Tests (30%)**
   - **Scope:** Full API request lifecycles connecting the FastAPI app to its real backend stores.
   - **Framework:** `pytest` + `testcontainers` + `httpx.AsyncClient`
   - **Setup:** Automatically spins up ephemeral Docker containers for Postgres, Redis, and Qdrant before running the suite. Alembic migrations are executed on the fly.
   - **Goal:** Verify that SQL queries, network connections, and multi-tenant RLS boundaries function correctly under real-world conditions.
   
3. **E2E & Frontend Tests (10%)**
   - **Scope:** Simulated user journeys through the Next.js web application.
   - **Framework:** `Playwright`
   - **Goal:** Render the DOM, click buttons, and verify SSE (Server-Sent Events) streaming responses appear on the UI.

## Specialized Testing Layers

### Performance Testing (Locust)
- Handled via `locustfile_chat.py` and `locustfile_ingestion.py`.
- Evaluates p95 latency under high concurrent load (e.g., 100 parallel chat users).

### RAG Evaluation (RAGAS)
- Operates on a `golden_dataset.json`.
- Evaluates the LLM's faithfulness to the context (preventing hallucinations) using an AI-as-a-Judge mechanism (GPT-4o).
- Runs weekly to track model drift without incurring excessive token costs on every PR.
