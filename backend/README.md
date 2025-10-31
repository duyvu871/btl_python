# Backend API - BTL Python Project

Backend service cho dự án BTL Python được xây dựng với FastAPI, gRPC, PostgreSQL, Redis, và Qdrant.

## 📋 Mục Lục

- [Công Nghệ Sử Dụng](#công-nghệ-sử-dụng)
- [Kiến Trúc Dự Án](#kiến-trúc-dự-án)
- [Cài Đặt](#cài-đặt)
- [Cấu Hình](#cấu-hình)
- [Chạy Ứng Dụng](#chạy-ứng-dụng)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)

## 🚀 Công Nghệ Sử Dụng

### Core Framework
- **FastAPI** - Modern web framework cho Python
- **gRPC** - High-performance RPC framework
- **SQLAlchemy 2.0** - SQL toolkit và ORM
- **Alembic** - Database migration tool

### Databases & Caching
- **PostgreSQL** - Primary database
- **Redis** - Caching và message queue
- **Qdrant** - Vector database cho AI/ML

### AI/ML Stack
- **LangChain** - Framework cho LLM applications
- **OpenAI API** - Language models
- **Google GenAI** - Google AI models

### Security
- **JWT** - JSON Web Tokens cho authentication
- **Argon2** - Password hashing
- **Email Validator** - Email validation

### Task Queue & Monitoring
- **ARQ** - Async task queue với Redis
- **Sentry** - Error tracking và monitoring

### Development Tools
- **UV** - Fast Python package installer
- **Pytest** - Testing framework
- **Ruff** - Fast Python linter
- **MkDocs** - Documentation generator

## 🏗️ Kiến Trúc Dự Án

Dự án theo mô hình **Clean Architecture** với các layer:

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI/gRPC)       │
├─────────────────────────────────────────┤
│          Use Cases (Business Logic)     │
├─────────────────────────────────────────┤
│          Repository Layer               │
├─────────────────────────────────────────┤
│          Database Layer (SQLAlchemy)    │
└─────────────────────────────────────────┘
```

### Design Patterns
- **Repository Pattern** - Trừu tượng hóa data access
- **Use Case Pattern** - Encapsulate business logic
- **Dependency Injection** - FastAPI DI system
- **Base Repository** - Shared repository methods

## 📦 Cài Đặt

### Yêu Cầu Hệ Thống
- Python >= 3.10
- Docker & Docker Compose
- UV package manager (recommended)

### Clone Repository
```bash
git clone <repository-url>
cd btl_python/backend
```

### Cài Đặt Dependencies

#### Sử dụng UV (Recommended)
```bash
# Cài đặt UV nếu chưa có
curl -LsSf https://astral.sh/uv/install.sh | sh

# Cài đặt dependencies
uv sync
```

#### Sử dụng Pip
```bash
pip install -e .
```

## ⚙️ Cấu Hình

### Environment Variables

Tạo file `.env.dev` trong thư mục root:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_DB=btl_oop_dev

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379

# Qdrant
QDRANT_URL=http://localhost:6333

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
FRONTEND_URL=http://localhost:5173

# Email (SMTP)
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=BTL Python

# ARQ Worker
ARQ_QUEUE_NAME=arq:queue
ARQ_MAX_JOBS=10
ARQ_JOB_TIMEOUT=300

# Sentry (Optional)
SENTRY_DSN=your-sentry-dsn

# Loki Logging (Optional)
LOKI_URL=http://localhost:3100
ENABLE_LOKI_LOGGING=False

# Debug
DEBUG=True
```

## 🚀 Chạy Ứng Dụng

### Development với Docker Compose

```bash
# Chạy tất cả services (backend, frontend, databases)
docker-compose -f docker-compose.dev.yml up -d

# Chỉ chạy backend services
docker-compose -f docker-compose.dev.yml up fastapi postgres redis qdrant -d

# Xem logs
docker-compose -f docker-compose.dev.yml logs -f fastapi
```

### Local Development (Không dùng Docker)

#### 1. Chạy Dependencies
```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=btl_oop_dev \
  postgres:15

# Redis
docker run -d -p 6379:6379 redis:alpine

# Qdrant
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

#### 2. Database Migration
```bash
# Chạy migrations
uv run alembic upgrade head

# Tạo migration mới
uv run alembic revision --autogenerate -m "description"
```

#### 3. Chạy FastAPI Server
```bash
# Development mode với auto-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### 4. Chạy gRPC Server
```bash
uv run python -m src.grpc_server
```

#### 5. Chạy ARQ Worker
```bash
uv run arq src.workers.send_mail.WorkerSettings
```

## 📚 API Documentation

### Interactive API Docs

- **Scalar UI**: http://localhost:8000/scalar
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### gRPC Services

gRPC server chạy trên port `50051`.

#### Available Services
- **AuthService**: Authentication và authorization
  - Register
  - Login
  - Token verification

## 🧪 Testing

```bash
# Chạy tất cả tests
uv run pytest

# Chạy với coverage
uv run pytest --cov=src --cov-report=html

# Chạy specific test file
uv run pytest tests/test_main.py

# Chạy với verbose
uv run pytest -v
```

## 📁 Cấu Trúc Thư Mục

```
backend/
├── alembic.ini                 # Alembic configuration
├── Dockerfile                  # Production Dockerfile
├── Dockerfile.dev              # Development Dockerfile
├── pyproject.toml              # Project dependencies & config
├── mkdocs.yml                  # Documentation config
├── uv.lock                     # UV lock file
│
├── src/                        # Source code
│   ├── main.py                 # FastAPI application entry
│   ├── grpc_server.py          # gRPC server entry
│   │
│   ├── api/                    # API layer
│   │   └── v1/                 # API version 1
│   │       └── main.py         # API router aggregation
│   │
│   ├── core/                   # Core functionality
│   │   ├── config/             # Configuration
│   │   │   └── env.py          # Environment variables
│   │   ├── database/           # Database setup
│   │   │   ├── db.py           # Database connection
│   │   │   └── models/         # SQLAlchemy models
│   │   │       └── user.py     # User model
│   │   ├── security/           # Security utilities
│   │   │   ├── jwt.py          # JWT handling
│   │   │   └── password.py     # Password hashing
│   │   └── utils/              # Utility functions
│   │       ├── number.py
│   │       └── santitize.py
│   │
��   ├── modules/                # Feature modules
│   │   ├── auth/               # Authentication module
│   │   │   ├── routing.py      # FastAPI routes
│   │   │   ├── grpc.py         # gRPC service
│   │   │   ├── schemas.py      # Pydantic schemas
│   │   │   └── use_cases/      # Business logic
│   │   │       └── register_user_use_case.py
│   │   ├── user/               # User module
│   │   │   ├── repository.py   # User repository
│   │   │   ├── schemas/        # User schemas
│   │   │   └── use_cases/      # User business logic
│   │   ├── email/              # Email module
│   │   └── grpc/               # Generated gRPC code
│   │       └── speech_hub/     # gRPC proto generated files
│   │
│   └── shared/                 # Shared code
│       ├── base/               # Base classes
│       │   └── base_repository.py
│       └── schemas/            # Common schemas
│           └── response.py     # API response schemas
│
├── templates/                  # Email templates
│   └── emails/
│       ├── verification.html
│       ├── verification.txt
│       ├── password_reset.html
│       └── password_reset.txt
│
├── tests/                      # Tests
│   ├── __init__.py
│   └── test_main.py
│
├── docs/                       # MkDocs documentation
├── resources/                  # Static resources
└── scripts/                    # Utility scripts
```

### Module Structure

Mỗi module (auth, user, etc.) theo cấu trúc:

```
module_name/
├── routing.py          # FastAPI endpoints
├── grpc.py            # gRPC service implementation
├── schemas.py         # Request/Response schemas
├── repository.py      # Data access layer
└── use_cases/         # Business logic
    ├── __init__.py
    └── specific_use_case.py
```

## 🔧 Development Commands

### Database

```bash
# Tạo migration mới
uv run alembic revision --autogenerate -m "Add users table"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Show current revision
uv run alembic current

# Show migration history
uv run alembic history
```

### Linting & Formatting

```bash
# Lint code với Ruff
uv run ruff check .

# Format code
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Generate gRPC Code

```bash
# Generate Python code from proto files
bash ../scripts/generate_proto.sh
```

## 🔐 Security

- **Password Hashing**: Argon2
- **JWT Tokens**: HS256 algorithm
- **CORS**: Configured for specific origins
- **Input Validation**: Pydantic models
- **SQL Injection**: SQLAlchemy ORM
- **Rate Limiting**: (Planned)

## 📝 License

MIT License

## 👥 Contributors

- Bùi An Du - dubuicp123@gmail.com

## 📞 Support

Nếu có vấn đề hoặc câu hỏi, vui lòng tạo issue trên GitHub repository.

---

**Happy Coding! 🎉**

