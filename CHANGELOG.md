# Changelog

All notable changes to **OpenRAG** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Real email service with SMTP/SendGrid/Resend/SES support (`app/services/email.py`)
- SMTP configuration fields to `Settings` class and `.env.example`
- `FRONTEND_URL` setting for email link generation
- `HEALTHCHECK` directive to backend `Dockerfile`
- `docs/TROUBLESHOOTING.md` — comprehensive troubleshooting guide
- `docs/FAQ.md` — frequently asked questions
- `.github/ISSUE_TEMPLATE/config.yml` — disable blank issues, direct to discussions
- `.github/ISSUE_TEMPLATE/bug_report.yml` — structured GitHub Form bug report
- `.github/ISSUE_TEMPLATE/feature_request.yml` — structured GitHub Form feature request
- `.github/ISSUE_TEMPLATE/question.yml` — Q&A issue template
- `frontend/public/og-image.png` — branded social preview image
- Multi-arch Docker builds (`linux/amd64,linux/arm64`) in release workflow
- Codecov coverage upload step in CI pipeline
- Playwright browser installation step in CI
- Community & Support table in README
- `codecov` and `multi-arch` badges in README

### Changed
- Coverage gate raised from 70% → **80%** in CI
- OG image metadata: replaced `via.placeholder.com` with real `/og-image.png`
- Frontend `metadata` enriched: keywords, authors, robots, canonical, OG site name
- NOTICE file: comprehensive third-party attributions for all major dependencies
- README: added Codecov and multi-arch badges, Community section

### Fixed
- Password reset endpoint now sends real emails (was logging mock to stdout)
- Playwright CI: added browser installation step and `CI=true` environment flag
- Release workflow: missing `platforms` directive (was not actually multi-arch)
- `python-jose` tagged for migration to PyJWT (unmaintained library)

### Security
- `Dockerfile` `HEALTHCHECK` added — containers now report unhealthy state instead of appearing healthy while broken

---

## [0.1.0] - 2026-06-30

### Added
- **Multi-Tenant Architecture**: Full database-level Row-Level Security (RLS) integration.
- **Security Audit Logs**: Async background middleware tracking all mutating API calls.
- **Hybrid RAG**: Dense (Qdrant) + Sparse (BM25 via Redis) Retrieval with Reciprocal Rank Fusion (RRF).
- **HyDE Query Augmentation**: Hypothetical Document Embedding for improved retrieval recall.
- **Freshness Boosting**: 20% multiplicative boost for documents indexed within 30 days.
- **MFA Login**: TOTP (RFC 6238) endpoints: setup, verify, and MFA-gated login.
- **JWT Refresh Token Rotation**: Old tokens blacklisted in Redis on every refresh.
- **Timing-Attack Prevention**: Dummy hash verify on failed login to equalize response times.
- **SAML 2.0 / OIDC SSO**: Enterprise SSO via `authlib` and `python3-saml`.
- **SSE Streaming Chat**: Server-Sent Events with per-source citation grounding.
- **Ragas Evaluation**: Automated context precision/recall testing pipeline.
- **Test Infrastructure**: Testcontainers (Integration), Playwright (E2E), Locust (Load).
- **Full Observability**: OpenTelemetry, Prometheus, Grafana, Loki, Langfuse.
- **Helm Charts**: Kubernetes deployment with HPA and NetworkPolicy.
- **SDKs**: Python and TypeScript client scaffolding.
- **Docker Compose**: 16-service production stack with health checks.
- **CI/CD**: GitHub Actions pipelines (CI, CD, Release, Security Scan).
- **Trivy Container Scanning**: CRITICAL/HIGH CVEs block CI merges.
- **Bandit SAST**: Static analysis on every PR.
- **dependabot**: Automated dependency updates for pip, npm, Docker, GitHub Actions.

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
- Argon2id password hashing — PHC winner, current industry gold standard.

---

## [0.0.1] - 2026-06-01

### Added
- Initial project scaffolding (FastAPI, Next.js).
- Basic Ollama and LiteLLM integration.
- Docker Compose foundation.

[Unreleased]: https://github.com/ardamoustafa1/OpenRAG/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ardamoustafa1/OpenRAG/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/ardamoustafa1/OpenRAG/releases/tag/v0.0.1
