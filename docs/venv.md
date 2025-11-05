# Hướng dẫn Sử dụng Virtual Environment (venv)

## Tổng quan

Virtual Environment (venv) là một công cụ trong Python giúp tạo môi trường ảo để quản lý dependencies riêng biệt cho từng dự án, tránh xung đột giữa các gói thư viện.

Trong dự án này, venv được sử dụng để cô lập dependencies của backend và inference services.

## Tạo Virtual Environment

### Trên Linux/MacOS

```bash
# Tạo venv trong thư mục backend
uv venv backend/.venv

# Tạo venv trong thư mục s2t
uv venv s2t/.venv
```

### Trên Windows

```cmd
# Tạo venv trong thư mục backend
uv venv backend\.venv

# Tạo venv trong thư mục inference
uv venv inference\.venv
```

## Kích hoạt Virtual Environment

### Trên Linux/MacOS

```bash
# Kích hoạt venv của backend
source backend/.venv/bin/activate

# Kích hoạt venv của s2t
source s2t/.venv/bin/activate
```

### Trên Windows

```cmd
# Kích hoạt venv của backend
backend\.venv\Scripts\activate

# Kích hoạt venv của inference
inference\.venv\Scripts\activate
```

## Lưu ý về Shell không tương thích

Trên một số môi trường, lệnh `source` có thể không hoạt động nếu shell hiện tại không hỗ trợ (ví dụ: đang dùng zsh nhưng lệnh dành cho bash). Trong trường hợp này, sử dụng bash để kích hoạt và chuyển sang shell hiện tại:

```bash
# Ví dụ cho backend trên Linux/MacOS với zsh
bash -c "source backend/.venv/bin/activate && exec zsh"

# Hoặc cho s2t
bash -c "source inference/.venv/bin/activate && exec zsh"
```

## Tắt Virtual Environment

Để tắt venv, chạy lệnh:

```bash
deactivate
```

Lệnh này hoạt động trên cả Linux và Windows.

## Cài đặt Dependencies

Sau khi kích hoạt venv, cài đặt dependencies bằng uv:

```bash
# Trong backend
uv pip install .

# Trong s2t
uv pip install .
```

Hoặc sử dụng uv sync nếu có uv.lock:

```bash
# Trong backend
uv sync

# Trong s2t
uv sync
```

Hoặc sử dụng pip nếu cần:

```bash
pip install -r requirements.txt
```

## Kiểm tra venv đang hoạt động

Sau khi activate, prompt sẽ hiển thị tên venv (ví dụ: `(backend)` hoặc `(inference`)
