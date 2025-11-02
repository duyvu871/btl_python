# BTL Python Project - Speech-to-Text System

Dự án BTL (Bài Tập Lớn) Python - Hệ thống AI Speech-to-Text (S2T) với khả năng realtime và batch, tích hợp RAG cho hỏi đáp thông minh.

## Tổng Quan Dự Án

Dự án này xây dựng một hệ thống AI hoàn chỉnh cho chuyển đổi giọng nói thành văn bản, bao gồm:
- **Speech-to-Text (S2T)**: Realtime qua WebSocket và batch qua upload file với faster-whisper
- **Quản lý người dùng**: Đăng ký, đăng nhập, hồ sơ, gói dịch vụ với quota usage
- **Quản lý bản ghi**: Lưu trữ recordings và segments với timestamp
- **Hỏi đáp thông minh**: Semantic search và RAG trên transcripts với citations
- **Infrastructure**: Giám sát và logging với Grafana/Loki

## Cấu Trúc Dự Án

```
btl_python/
├── backend/           # Backend API service (FastAPI + gRPC + Celery)
├── frontend/          # Frontend application (Next.js + Tailwind)
├── inference/         # AI inference service (faster-whisper + RAG)
├── infras/            # Infrastructure (Grafana, Loki)
├── proto/             # Protocol buffer definitions
├── scripts/           # Utility scripts
├── docs/              # Documentation (requirements, etc.)
├── docker-compose.*   # Docker compose files
├── Makefile           # Build automation
├── package.json       # Node.js dependencies
├── README.md          # This file
└── WORKFLOW.md        # Development workflow
```

### Chi Tiết Các Thành Phần

- **backend/**: Host dịch vụ API chính với FastAPI, xử lý authentication, user management, recordings, và tích hợp với PostgreSQL, Redis, Qdrant. Bao gồm Celery cho batch processing.
- **frontend/**: Host giao diện web với Next.js, hỗ trợ realtime S2T qua WebSocket, upload batch, và giao diện hỏi đáp RAG.
- **inference/**: Host dịch vụ suy luận AI, chạy faster-whisper cho S2T, và xử lý RAG với embeddings và LLM.
- **infras/**: Cung cấp infrastructure cho monitoring và logging với Grafana dashboards và Loki.
- **proto/**: Chứa định nghĩa protobuf cho gRPC services (nếu cần mở rộng).
- **docs/**: Tài liệu chi tiết về requirements, kiến trúc, và mô hình dữ liệu.
- **scripts/**: Các script tiện ích cho development, deployment, và generate proto.

## Công Nghệ Chính

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Celery, PostgreSQL, Redis, Qdrant
- **AI/ML**: Faster-whisper, LangChain, OpenAI API, Google GenAI
- **Frontend**: Next.js, Tailwind CSS, shadcn/ui
- **Infrastructure**: Docker, Docker Compose, Nginx, Grafana, Loki
- **DevOps**: Makefile, GitHub Actions (CI/CD)

## Cách Chạy Dự Án

### Development

```bash
# Chạy toàn bộ hệ thống
docker-compose -f docker-compose.dev.yml up -d

# Hoặc chạy từng phần
make dev
```

### Production

```bash
# Build và deploy
make build
make deploy
```

## Tài Liệu Chi Tiết

Xem [docs/requirement.md](docs/requirement.md) cho thông tin chi tiết về:
- Phạm vi chức năng MVP
- Kiến trúc luồng dữ liệu
- Mô hình dữ liệu PostgreSQL
- Trigger và Procedure

## Đóng Góp

Xem [WORKFLOW.md](WORKFLOW.md) cho hướng dẫn development workflow.

## License

MIT License
