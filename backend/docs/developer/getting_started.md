# Developer Onboarding & Getting Started

Welcome to the Enterprise AI Platform backend team! This guide will get you from zero to running the API locally in under 5 minutes.

## Prerequisites
- Python 3.12+
- Docker Desktop or OrbStack (Ensure it is running!)
- Git
- VS Code (with Ruff and Python extensions recommended)

## Step-by-Step Setup

### Step 1: Clone and Configure
Clone the repository and copy the example environment file:
```bash
git clone https://github.com/your-org/ai-platform.git
cd ai-platform/backend
cp .env.example .env
```
*(Never put real production secrets in `.env`!)*

### Step 2: Spin Up Infrastructure
We use Docker Compose to run local versions of PostgreSQL, Redis, and Qdrant for development.
```bash
docker-compose up -d
```

### Step 3: Database Migrations & Seeding
Install Python dependencies, run Alembic migrations to create the tables, and seed the database with a test tenant and admin user.
```bash
make setup
make migrate
make seed
```

### Step 4: Run Tests
Ensure everything is working correctly before writing code.
```bash
make test-unit
make test-integration
```

### Step 5: Start the API
Start the FastAPI hot-reload server.
```bash
make dev
```
Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive Swagger UI.

## Contribution Guidelines
- **Branch Naming:** `feat/your-feature`, `fix/issue-description`, `chore/cleanup`
- **Commits:** We enforce Conventional Commits (e.g., `feat(auth): add MFA support`).
- **PRs:** All PRs must pass the CI pipeline (`ruff` linting, `mypy` typing, and 100% passing tests). Do not merge without at least 1 code review approval.
