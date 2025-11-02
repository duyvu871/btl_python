# Hướng dẫn Migration Database

## Tổng quan

Migration database được sử dụng để quản lý các thay đổi cấu trúc cơ sở dữ liệu một cách có hệ thống. Dự án này sử dụng Alembic để quản lý migration.

## Các lệnh Migration

### 1. Tạo Migration mới

Để tạo một migration mới dựa trên các thay đổi trong model:

```bash
make migrate-create
```

Lệnh này sẽ:
- Yêu cầu bạn nhập thông điệp cho migration.
- Tự động tạo file migration trong thư mục `backend/alembic/versions/` dựa trên sự khác biệt giữa model hiện tại và database schema.

### 2. Chạy Migration

Để áp dụng tất cả migration chưa được áp dụng lên database:

```bash
make migrate
```

Lệnh này sẽ chạy `alembic upgrade head` để nâng cấp database lên phiên bản mới nhất.

### 3. Seed Database

Để thêm dữ liệu ban đầu vào database sau khi migration:

```bash
make seed
```

Lệnh này sẽ chạy script `scripts/seed_admin.py` để seed dữ liệu admin ban đầu.

## Lưu ý

- Đảm bảo rằng môi trường development đang chạy trước khi thực hiện migration (sử dụng `make dev`).
- Luôn kiểm tra file migration được tạo tự động trước khi commit.
- Nếu có lỗi, kiểm tra log của container FastAPI bằng `make logs-api`.
