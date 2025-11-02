# Generate gRPC Python code from .proto files for both backend and inference services.
PROTO_DIR:=proto
BACKEND_OUT:=backend
INFER_OUT:=inference
PROTO_FILES:=$(patsubst $(PROTO_DIR)/%,%,$(shell find $(PROTO_DIR) -name '*.proto'))

# python path to the virtual environment
BACKEND_PYTHON_PATH?=backend/.venv/bin/python
INFER_PYTHON_PATH?=inference/.venv/bin/python

# Check if the specified Python paths
define CHECK_PYTHON_PATH
  if [ ! -f $(1) ]; then \
    echo "Error: Python path '$(1)' does not exist. Please set the correct path."; \
    exit 1; \
  fi
endef

# generate gRPC code for backend and inference
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
proto-backend:
	$(call GENERATE_GRPC_CODE, $(BACKEND_PYTHON_PATH), $(BACKEND_OUT))

proto-inference:
	$(call GENERATE_GRPC_CODE, $(INFER_PYTHON_PATH), $(INFER_OUT))

proto-all: proto-backend proto-inference

# docker targets
.PHONY: dev prod up down down-prod build build-prod rebuild rebuild-prod logs logs-api logs-fe logs-worker logs-db shell

dev:
	docker compose -f docker-compose.dev.yml --env-file .env.dev up -d

prod:
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

up: dev

down:
	docker compose -f docker-compose.dev.yml down

down-prod:
	docker compose -f docker-compose.prod.yml down

build:
	docker compose -f docker-compose.dev.yml --env-file .env.dev build

build-prod:
	docker compose -f docker-compose.prod.yml --env-file .env.prod build

rebuild:
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.dev.yml --env-file .env.dev build --no-cache
	docker compose -f docker-compose.dev.yml --env-file .env.dev up -d

rebuild-prod:
	docker compose -f docker-compose.prod.yml down
	docker compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

logs:
	docker compose -f docker-compose.dev.yml logs -f

logs-api:
	docker compose -f docker-compose.dev.yml logs -f fastapi

logs-fe:
	docker compose -f docker-compose.dev.yml logs -f frontend

# start monitoring services
monitor-up:
	docker compose -f docker-compose.monitor.yml up -d

# stop monitoring services
monitor-down:
	docker compose -f docker-compose.monitor.yml down

# Rebuild and restart
rebuild:
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml --env-file .env.dev build --no-cache
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Rebuild and restart production
rebuild-prod:
	docker-compose -f docker-compose.prod.yml down
	docker-compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Show logs from all services
logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Show logs from FastAPI service only
logs-api:
	docker-compose -f docker-compose.dev.yml logs -f fastapi

# Show logs from Frontend service
logs-fe:
	docker-compose -f docker-compose.dev.yml logs -f frontend

# Show logs from worker service
logs-worker:
	docker-compose -f docker-compose.dev.yml logs -f worker_send_mail

# Show logs from PostgreSQL
logs-db:
	docker-compose -f docker-compose.dev.yml logs -f postgres

# Open shell in FastAPI container
shell:
	docker-compose -f docker-compose.dev.yml exec fastapi bash

# Open shell in Frontend container
shell-fe:
	docker-compose -f docker-compose.dev.yml exec frontend sh

# Open PostgreSQL shell
db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U $$(grep POSTGRES_USER .env.dev | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env.dev | cut -d '=' -f2)

# Open Redis CLI
redis-shell:
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# Remove all containers and volumes
clean:
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

# Seed database
seed:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/seed_admin.py


# Database migrations
migrate:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic revision --autogenerate -m "$$msg"

# Run tests
test:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run pytest

# Start documentation server
docs:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run mkdocs serve -f mkdocs.yml

# Run linting
lint:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run ruff check .
	docker-compose -f docker-compose.dev.yml exec frontend npm run lint

# Format code
format:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run ruff format .
	docker-compose -f docker-compose.dev.yml exec frontend npm run format