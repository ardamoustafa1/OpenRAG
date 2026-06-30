.PHONY: help up down logs build migrate lint format test-unit test-integration test-e2e test-load test-rag test-all clean

# Default target
help: ## Show this help message
	@echo ""
	@echo "Enterprise RAG AI Platform — Make Commands"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ─── Infrastructure ────────────────────────────────────────────────────────────

up: ## Start all services (dev mode with hot-reload)
	docker compose up -d
	@echo "✅ All services started. Frontend: http://localhost:3000 | API Docs: http://api.localhost/docs"

up-gpu: ## Start all services including GPU/vLLM profile
	docker compose --profile gpu up -d

down: ## Stop all services
	docker compose down

down-clean: ## Stop services and remove all volumes (DESTROYS DATA)
	docker compose down -v --remove-orphans

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs for all services
	docker compose logs -f

logs-backend: ## Tail backend logs only
	docker compose logs -f backend

logs-celery: ## Tail celery worker logs
	docker compose logs -f celery_worker

ps: ## Show status of all services
	docker compose ps

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run Alembic database migrations
	docker compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="your message")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Show migration history
	docker compose exec backend alembic history

migrate-rollback: ## Rollback one migration step
	docker compose exec backend alembic downgrade -1

# ─── Build ────────────────────────────────────────────────────────────────────

build: ## Build all Docker images
	docker compose build

build-backend: ## Build backend Docker image only
	docker build -t OpenRAG-backend:dev ./backend

build-frontend: ## Build frontend Docker image only
	docker build -t OpenRAG-frontend:dev ./frontend

# ─── Linting ──────────────────────────────────────────────────────────────────

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend (ruff + mypy + bandit)
	cd backend && ruff check .
	cd backend && mypy app/
	cd backend && bandit -r app/ -ll

lint-frontend: ## Lint frontend (eslint + tsc)
	cd frontend && npm run lint
	cd frontend && npx tsc --noEmit

format: ## Auto-format code (ruff + black)
	cd backend && ruff check --fix .
	cd backend && black .

# ─── Testing ──────────────────────────────────────────────────────────────────

test-unit: ## Run backend unit tests
	cd backend && pytest tests/unit/ -n auto --cov=app --cov-report=term-missing

test-integration: ## Run backend integration tests (requires Docker)
	cd backend && pytest tests/integration/ -v

test-security: ## Run security tests
	cd backend && pytest tests/security/ -v

test-e2e: ## Run Playwright E2E tests
	cd frontend && npx playwright test

test-load: ## Run Locust load test (100 users, 10 min)
	cd backend && locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 10m

test-rag: ## Run RAG evaluation (RAGAS metrics)
	cd backend && python tests/rag_evaluation/evaluate_rag.py

test-all: test-unit test-integration test-e2e test-rag ## Run entire test suite

# ─── Utilities ────────────────────────────────────────────────────────────────

shell-backend: ## Open a bash shell in the backend container
	docker compose exec backend bash

shell-db: ## Open psql in the postgres container
	docker compose exec postgres psql -U postgres -d rag_db

audit: ## Run dependency security audits
	cd backend && pip-audit
	cd frontend && npm audit --audit-level=high

clean: ## Remove Python __pycache__ and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.mypy_cache backend/.pytest_cache backend/htmlcov
	rm -rf frontend/.next frontend/node_modules/.cache
