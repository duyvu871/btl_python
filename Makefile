# Generate gRPC Python code from .proto files for both backend and s2t services.
PROTO_DIR:=proto
BACKEND_OUT:=backend
INFER_OUT:=s2t
PROTO_FILES:=$(patsubst $(PROTO_DIR)/%,%,$(shell find $(PROTO_DIR) -name '*.proto'))

# python path to the virtual environment
BACKEND_PYTHON_PATH?=backend/.venv/bin/python
INFER_PYTHON_PATH?=s2t/.venv/bin/python

# Check if the specified Python paths
define CHECK_PYTHON_PATH
  if [ ! -f $(1) ]; then \
    echo "Error: Python path '$(1)' does not exist. Please set the correct path."; \
    exit 1; \
  fi
endef

# generate gRPC code for backend and s2t
define GENERATE_GRPC_CODE
  $(call CHECK_PYTHON_PATH, $(1))
  @echo "Generating gRPC code in $(2)..."
  $(1) -m grpc_tools.protoc -I $(PROTO_DIR) \
    --pyi_out $(2) --python_out $(2) --grpc_python_out $(2) \
    $(PROTO_FILES)
  @echo "gRPC code generation completed for $(2)."
endef

.PHONY: proto-backend proto-inference proto-all

# proto generation targets
proto-backend: ## Generate gRPC code for backend service
	$(call GENERATE_GRPC_CODE, $(BACKEND_PYTHON_PATH), $(BACKEND_OUT))

proto-s2t: ## Generate gRPC code for s2t service
	$(call GENERATE_GRPC_CODE, $(INFER_PYTHON_PATH), $(INFER_OUT))

proto-all: proto-backend proto-s2t ## Generate gRPC code for both backend and s2t services

# docker targets
.PHONY: dev prod up down down-prod build build-prod rebuild rebuild-prod logs logs-api logs-fe logs-worker logs-db shell

dev: ## Start development environment with docker-compose.dev.yml
	docker compose -f docker-compose.dev.yml --env-file .env.dev up -d

prod: ## Start production environment with docker-compose.prod.yml
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

up: dev ## Alias for dev

down: ## Stop development environment
	docker compose -f docker-compose.dev.yml down

down-prod: ## Stop production environment
	docker compose -f docker-compose.prod.yml down

build: ## Build development containers
	docker compose -f docker-compose.dev.yml --env-file .env.dev build

build-prod: ## Build production containers
	docker compose -f docker-compose.prod.yml --env-file .env.prod build

rebuild: ## Rebuild and restart development environment
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.dev.yml --env-file .env.dev build --no-cache
	docker compose -f docker-compose.dev.yml --env-file .env.dev up -d

rebuild-prod: ## Rebuild and restart production environment
	docker compose -f docker-compose.prod.yml down
	docker compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

logs: ## Show logs from all development services
	docker compose -f docker-compose.dev.yml logs -f

logs-api: ## Show logs from FastAPI service
	docker compose -f docker-compose.dev.yml logs -f fastapi

logs-fe: ## Show logs from Frontend service
	docker compose -f docker-compose.dev.yml logs -f frontend

# start monitoring services
monitor-up: ## Start monitoring services (Grafana, Loki)
	docker compose -f docker-compose.monitor.yml up -d

# stop monitoring services
monitor-down: ## Stop monitoring services
	docker compose -f docker-compose.monitor.yml down

# Show logs from worker service
logs-worker: ## Show logs from worker_send_mail service
	docker compose -f docker-compose.dev.yml logs -f worker_send_mail

# Show logs from PostgreSQL
logs-db: ## Show logs from PostgreSQL database
	docker compose -f docker-compose.dev.yml logs -f postgres

# Open shell in FastAPI container
shell: ## Open bash shell in FastAPI container
	docker compose -f docker-compose.dev.yml exec fastapi bash

# Open shell in Frontend container
shell-fe: ## Open sh shell in Frontend container
	docker compose -f docker-compose.dev.yml exec frontend sh

# Open PostgreSQL shell
db-shell: ## Open PostgreSQL shell
	docker compose -f docker-compose.dev.yml exec postgres psql -U $$(grep POSTGRES_USER .env.dev | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env.dev | cut -d '=' -f2)

# Open Redis CLI
redis-shell: ## Open Redis CLI
	docker compose -f docker-compose.dev.yml exec redis redis-cli

# Remove all containers and volumes
clean: ## Clean up containers, volumes, and prune system
	docker compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

# Seed database
seed: ## Seed database with initial data
	docker compose -f docker-compose.dev.yml exec fastapi uv run python scripts/seed_admin.py

# Database migrations
migrate: ## Run database migrations
	docker compose -f docker-compose.dev.yml exec fastapi uv run alembic upgrade head

migrate-create: ## Create new database migration
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	docker compose -f docker-compose.dev.yml exec fastapi uv run alembic revision --autogenerate -m "$$msg"

# Run tests
test: ## Run pytest tests
	docker compose -f docker-compose.dev.yml exec fastapi uv run pytest

# Start documentation server
docs: ## Start MkDocs documentation server
	docker compose -f docker-compose.dev.yml exec fastapi uv run mkdocs serve -f mkdocs.yml

# Run linting
lint: ## Run linting for backend and frontend
	docker compose -f docker-compose.dev.yml exec fastapi uv run ruff check .
	docker compose -f docker-compose.dev.yml exec frontend npm run lint

# Format code
format: ## Format code for backend and frontend
	docker compose -f docker-compose.dev.yml exec fastapi uv run ruff format .
	docker compose -f docker-compose.dev.yml exec frontend npm run format

# Help target
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'
