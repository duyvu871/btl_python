# BTL Python - Speech-to-Text Application

## Quick Start

### Development

```bash
# Clone repository
git clone <your-repo-url>
cd btl_python

# Copy environment files
cp .env.dev .env.dev

# Start all services
make dev

# Or manually
docker compose -f docker-compose.dev.yml up -d

# View logs
make logs

# Access services:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/scalar
# - MinIO Console: http://localhost:9001
```

### Production

```bash
# Setup environment
cp .env.example .env
cp .env.s2t.example .env.s2t

# Edit .env and .env.s2t - CHANGE ALL PASSWORDS AND SECRETS!

# Build and start
make prod-build
make prod-up

# Run migrations
make prod-migrate

# Create admin user
make prod-create-admin

# Check health
make health

# Access services:
# - Frontend: http://localhost
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/scalar
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                     Nginx + Vite Build                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (REST)                     │
│              Auth, Record, Subscription APIs                 │
└───────┬────────────────────────────┬────────────────────────┘
        │                            │
        ▼                            ▼
┌──────────────────┐        ┌──────────────────┐
│   gRPC Server    │        │  S2T Service     │
│  Record Service  │        │  Transcription   │
└──────────────────┘        └──────────────────┘
        │                            │
        └────────────┬───────────────┘
                     │
        ┌────────────┴────────────┐
        ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │Postgres│  │ Redis  │  │ Qdrant │
    └────────┘  └────────┘  └────────┘
                     ▼
                ┌────────┐
                │ MinIO  │
                └────────┘
```

## Features

- 🎤 **Speech-to-Text**: Real-time and file upload transcription
- 🌐 **Multi-language**: Vietnamese and English support
- 🔐 **Authentication**: JWT-based auth with email verification
- 💳 **Subscription**: Usage tracking and plan management
- 🔍 **Search**: Full-text search in transcripts using vector database
- 📊 **Analytics**: Recording statistics and usage monitoring
- 📧 **Email**: Async email notifications via ARQ worker
- 🗄️ **Storage**: MinIO object storage for audio files

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database
- **Redis**: Cache and message queue
- **Qdrant**: Vector database for semantic search
- **MinIO**: S3-compatible object storage
- **gRPC**: Inter-service communication
- **ARQ**: Async task queue

### Frontend
- **React 19**: UI library
- **Vite**: Build tool
- **Mantine v8**: Component library
- **TanStack Query**: Data fetching
- **Jotai**: State management
- **React Router**: Client-side routing

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving
- **Loki + Grafana**: Logging and monitoring (optional)

## Development

### Prerequisites
- Docker Engine 20.10+
- Docker Compose V2
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Available Make Commands

```bash
make help                 # Show all available commands

# Development
make dev                  # Start dev environment
make down                 # Stop dev environment
make logs                 # View all logs
make logs-api             # View API logs
make shell                # Open shell in API container

# Production
make prod-up              # Start production
make prod-down            # Stop production
make prod-build           # Build production images
make prod-migrate         # Run migrations
make prod-backup-db       # Backup database
make prod-logs            # View production logs

# Monitoring
make monitor-up           # Start Grafana + Loki
make health               # Check all services health

# Cleanup
make clean                # Remove stopped containers
make clean-volumes        # Remove unused volumes
```

### Project Structure

```
btl_python/
├── backend/              # FastAPI application
│   ├── src/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core utilities
│   │   ├── modules/      # Business logic modules
│   │   └── shared/       # Shared utilities
│   ├── alembic/          # Database migrations
│   ├── scripts/          # Utility scripts
│   ├── tests/            # Tests
│   └── Dockerfile
├── frontend/             # React application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── api/          # API client
│   │   ├── hooks/        # Custom hooks
│   │   └── store/        # State management
│   ├── public/           # Static assets
│   └── Dockerfile
├── s2t/                  # Speech-to-Text service
│   ├── src/
│   └── Dockerfile
├── proto/                # gRPC protocol definitions
├── infras/               # Infrastructure configs
│   ├── grafana/
│   └── loki/
├── docker-compose.yml    # Production compose
├── docker-compose.dev.yml # Development compose
├── Makefile              # Build commands
├── DEPLOYMENT.md         # Deployment guide
└── README.md             # This file
```

## API Documentation

- **Scalar UI**: http://localhost:8000/scalar
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Main Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/record/upload` - Upload audio for transcription
- `GET /api/v1/record` - List recordings
- `GET /api/v1/record/{id}/transcript` - Get transcript
- `POST /api/v1/record/search` - Search in transcripts

## Environment Variables

See `.env.example` for all available environment variables.

**Critical variables to change in production:**
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `SMTP_PASSWORD`
- `CORS_ORIGINS`

## Database Migrations

```bash
# Development
docker compose -f docker-compose.dev.yml exec fastapi uv run alembic upgrade head

# Production
make prod-migrate
```

## Testing

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

## Monitoring

Enable monitoring stack:

```bash
make monitor-up
```

Access:
- **Grafana**: http://localhost:3000
- **Loki**: http://localhost:3100

## Backup & Restore

### Database Backup
```bash
make prod-backup-db
# Creates backup in backups/backup_YYYYMMDD_HHMMSS.sql
```

### Database Restore
```bash
make prod-restore-db FILE=backups/backup_20240101_120000.sql
```

### MinIO Backup
```bash
make prod-backup-minio
# Creates backup in backups/minio_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment guide.

## Troubleshooting

### Service won't start
```bash
# Check logs
make logs-api

# Check service status
make ps
```

### Database connection error
```bash
# Verify PostgreSQL is healthy
docker compose exec postgres pg_isready -U postgres
```

### Frontend can't connect to API
- Check `VITE_API_BASE_URL` in frontend `.env`
- Verify CORS settings in backend `.env`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check documentation in `/docs`
- Review logs with `make logs`

## Authors

BTL PYTHON - PTIT Team

