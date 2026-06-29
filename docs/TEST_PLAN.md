# Enterprise RAG Platform - Test Plan

## Overview
This document outlines the testing strategy for the Enterprise RAG Platform. Our goal is to achieve >70% test coverage across Unit, Integration, End-to-End, and Performance vectors, ensuring a stable, scalable, and secure deployment.

## 1. Unit Testing
**Tooling**: `pytest`, `pytest-asyncio`, `pytest-cov`
**Scope**:
- Authentication utilities (JWT creation/validation, hashing logic)
- Schema validations (Pydantic models)
- Core utility functions (token counters, string cleaners)
**Execution**: `pytest tests/unit/ --cov=app`

## 2. Integration Testing
**Tooling**: `pytest`, `httpx` (AsyncClient), `testcontainers`
**Scope**:
- API Endpoint behavioral tests
- Database migrations and ORM operations
- Background task triggering (Celery)
**Architecture**: 
`testcontainers` is used to spin up ephemeral PostgreSQL, Redis, and Qdrant instances. This guarantees that integration tests run in a pristine state and do not pollute developer databases.
**Execution**: `pytest tests/integration/`

## 3. End-to-End (E2E) Testing
**Tooling**: `Playwright` (Chromium, WebKit, Firefox)
**Scope**:
- User authentication flows (Login, MFA, Session Expiry)
- Chat interface interactions (sending queries, rendering markdown, citing sources)
- Admin panel tenant management
**Execution**: `npx playwright test`

## 4. Performance & Load Testing
**Tooling**: `Locust`
**Scope**:
- Simulating concurrent user connections to the SSE chat stream.
- Identifying database bottlenecks during high-volume document ingestion.
**Execution**: `locust -f tests/performance/locustfile.py --headless -u 100 -r 10`

## 5. RAG Evaluation (Generative Quality)
**Tooling**: `Ragas`
**Scope**:
- **Context Precision**: Did the retriever fetch the most relevant documents?
- **Context Recall**: Were all necessary facts retrieved?
- **Faithfulness**: Is the generated answer hallucination-free and purely based on the context?
- **Answer Relevancy**: Does the answer directly address the user's query?
**Execution**: `python tests/rag_evaluation/evaluate_rag.py`

## Continuous Integration (CI)
All tests (excluding long-running Load tests) are automated via GitHub Actions (`.github/workflows/ci.yml`). 
- **Blockers**: A PR cannot be merged if unit test coverage drops below 70% or if any E2E tests fail.
