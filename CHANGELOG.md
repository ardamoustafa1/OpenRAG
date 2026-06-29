# Changelog

All notable changes to the **Enterprise RAG AI Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Multi-Tenant Architecture**: Full database-level Row-Level Security (RLS) integration.
- **Security Audit Logs**: Async background middleware tracking all mutating API calls.
- **Hybrid RAG**: Integrated Dense (Qdrant) and Sparse (BM25 via Redis) Retrieval with Reciprocal Rank Fusion (RRF).
- **MFA Login**: Added Time-based One-Time Password (TOTP) endpoints.
- **Ragas Evaluation**: Script added for automated context precision and recall testing.
- **Test Infrastructure**: Testcontainers (Integration), Playwright (E2E), and Locust (Load) integrated.
- **Helm Charts**: Starter files for Kubernetes deployment.
- **SDKs**: Python and TypeScript client scaffolding.

### Fixed
- Disabled Swagger (`/docs`) in production environment.
- Corrected Stripe webhook payload verification logic.
- Prevented full JWT string from being stored in Redis blacklist; uses SHA256 hashes instead.
- Migrated API Key hashing from Argon2 to SHA256 to prevent DoS vulnerabilities during high traffic.
- Resolved duplicate endpoints and middleware mounts in `main.py`.

### Security
- Created `.env.example` to enforce secret definitions and `.gitignore` to prevent secret leaks.
- Enforced strict origin checks (`CORS_ALLOW_ORIGINS`) and TrustedHost middleware rules.
- Set up automated Bandit security scans in CI pipeline.

## [0.0.1] - 2026-06-01
### Added
- Initial project scaffolding (FastAPI, Next.js).
- Basic Ollama and LiteLLM integration.
