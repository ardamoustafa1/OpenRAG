# Contributing to Enterprise RAG AI Platform

Thank you for your interest in contributing! This document explains how to participate effectively.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branching Strategy](#branching-strategy)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)
- [Security Issues](#security-issues)
- [Release Process](#release-process)

---

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to maintaining a welcoming community.

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/enterprise-rag.git
   cd enterprise-rag
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/your-org/enterprise-rag.git
   ```

---

## Development Setup

### Prerequisites
- Docker & Docker Compose (v2.x+)
- Python 3.12+
- Node.js 20+
- GNU Make

### Quick Start (All Services)
```bash
cp .env.example .env
# Edit .env and set all REQUIRED values (SECRET_KEY, POSTGRES_PASSWORD, etc.)
make up
```

### Backend Only
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install ".[dev]"
# Copy env
cp ../.env .env
uvicorn app.main:app --reload
```

### Frontend Only
```bash
cd frontend
npm ci
npm run dev
```

### Useful Make Commands
| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Tail all service logs |
| `make migrate` | Run Alembic migrations |
| `make lint` | Run all linters |
| `make test-unit` | Run unit tests |
| `make test-integration` | Run integration tests |
| `make test-e2e` | Run Playwright E2E tests |
| `make test-all` | Run entire test suite |

---

## Branching Strategy

We follow **GitHub Flow**:

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code. Protected. Requires PR + review. |
| `feature/your-feature-name` | New features |
| `fix/issue-description` | Bug fixes |
| `docs/topic` | Documentation-only changes |
| `chore/task` | Maintenance tasks (deps, CI, etc.) |

**Branch naming examples:**
- `feature/bm25-sparse-retrieval`
- `fix/qdrant-healthcheck-timeout`
- `docs/deployment-guide`

---

## Commit Messages

We follow **[Conventional Commits](https://www.conventionalcommits.org/)** specification.

### Format
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types
| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Formatting, missing semicolons (no code change) |
| `refactor` | Code refactor (not a fix or feature) |
| `test` | Adding or updating tests |
| `chore` | Dependency updates, CI, tooling |
| `perf` | Performance improvements |
| `security` | Security fixes |

### Examples
```
feat(rag): add BM25 sparse retrieval with RRF merge
fix(auth): prevent timing attack in login endpoint
docs(deployment): add Kubernetes production guide
security(api): restrict CORS allow_headers to explicit list
```

### Breaking Changes
Add `BREAKING CHANGE:` in the commit footer:
```
feat(api)!: restructure document upload endpoint

BREAKING CHANGE: The upload endpoint now accepts multipart/form-data
instead of base64-encoded JSON body.
```

---

## Pull Request Process

1. **Create a branch** from `main` following the naming convention above.
2. **Make your changes** — keep PRs focused and small.
3. **Write or update tests** — see [Testing Requirements](#testing-requirements).
4. **Run the full lint suite** locally:
   ```bash
   make lint
   ```
5. **Open a Pull Request** using the [PR template](.github/PULL_REQUEST_TEMPLATE.md).
6. **Ensure all CI checks pass** (Ruff, Mypy, Pytest, ESLint, Trivy, Bandit).
7. **Request a review** from at least one [CODEOWNER](.github/CODEOWNERS).
8. **Address review comments** promptly.

> PRs that fail CI will not be merged. Security-sensitive changes require sign-off from `@your-org/security-team`.

---

## Testing Requirements

### Backend
- **Unit tests**: Required for all new business logic. Place in `backend/tests/unit/`.
- **Integration tests**: Required for new API endpoints. Place in `backend/tests/integration/`.
- **Coverage gate**: PRs must not drop coverage below 70%.

```bash
# Run with coverage
cd backend
pytest tests/unit/ --cov=app --cov-report=term-missing
```

### Frontend
- **Component tests** for reusable components (future).
- **E2E tests** for critical user flows (login, chat, upload).

```bash
cd frontend
npx playwright test
```

### Security Tests
- **Bandit**: Static security scan (runs in CI).
- **Trivy**: Docker image vulnerability scan (runs in CI).
- For sensitive changes, run manually: `cd backend && bandit -r app/ -ll`

---

## Code Style

### Python (Backend)
- **Formatter**: [`black`](https://black.readthedocs.io/) (line length: 88)
- **Linter**: [`ruff`](https://docs.astral.sh/ruff/) with E, W, F, I, C, B rules
- **Type checker**: [`mypy`](https://mypy.readthedocs.io/) in strict mode
- **Run all**: `cd backend && ruff check . && mypy app/`

### TypeScript (Frontend)
- **Formatter**: Prettier (via ESLint config)
- **Linter**: ESLint with Next.js config
- **Run**: `cd frontend && npm run lint && npx tsc --noEmit`

### General
- No commented-out code in PRs.
- No `TODO` comments without a linked GitHub issue.
- Delete unused imports before submitting.

---

## Security Issues

**Do NOT open a public GitHub issue for security vulnerabilities.**

Please read [SECURITY.md](SECURITY.md) for our responsible disclosure policy. Security issues reported via private channels receive priority treatment and public acknowledgment.

---

## Release Process

Releases are managed by the core team and follow [Semantic Versioning](https://semver.org/):

1. Core team creates a `release/vX.Y.Z` branch.
2. CHANGELOG.md is updated following [Keep a Changelog](https://keepachangelog.com/).
3. PR is merged to `main`.
4. A git tag `vX.Y.Z` is pushed, triggering the [release workflow](.github/workflows/release.yml).
5. The release workflow builds multi-arch Docker images, packages Helm charts, and creates a GitHub Release with checksummed artifacts.
