# Protobuf

Thư mục `proto/` chứa đặc tả giao tiếp giữa các dịch vụ ở dạng Protocol Buffers. Đây là nguồn chân lý duy nhất (single source of truth) cho API nội bộ.

Cấu trúc module tuân theo quy ước `[TEN_DU_AN]/[TEN_SERVICE]/[PHIEN_BAN]`:

```plaintext
proto/
└── speech_hub/
    ├── auth/
    │   └── v1/
    │       └── auth_service.proto
    └── common/
        └── v1/
            └── types.proto
```

## 1. Tiền đề kỹ thuật

- Toolchain: `protoc` (qua `grpcio-tools`), Python ≥ 3.9.
- Cài đặt bộ sinh mã Python:

```bash
pip install --upgrade grpcio grpcio-tools protobuf
```

- Thư mục đích biên dịch (Python stubs):
  - Backend: `backend/src`
  - Inference: `inference/src`

## 2. Sinh mã (code generation)

Luôn chạy từ thư mục gốc repository để `--proto_path=proto` ánh xạ đúng.

Các tham số quan trọng:
- `--proto_path` (`-I`): gốc tìm kiếm .proto (ở đây: `proto/`).
- `--python_out`: nơi sinh các tệp `*_pb2.py`.
- `--grpc_python_out`: nơi sinh các tệp `*_pb2_grpc.py` (service stubs).

### 2.1. Backend (Python)

```bash
python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=backend/src \
  --grpc_python_out=backend/src \
  proto/speech_hub/common/v1/types.proto \
  proto/speech_hub/auth/v1/auth_service.proto
```

Sau khi sinh mã, import điển hình:

```python
from speech_hub.common.v1 import types_pb2
from speech_hub.auth.v1 import auth_service_pb2_grpc
```

### 2.2. Inference (Python)

```bash
python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=s2t/src \
  --grpc_python_out=s2t/src \
  proto/speech_hub/common/v1/types.proto \
  proto/speech_hub/auth/v1/auth_service.proto
```

> Khuyến nghị: dùng target Makefile để đảm bảo tái lập (xem Mục 4).

## 3. Quy ước package và import Python

- `package` trong `.proto` (ví dụ: `speech_hub.common.v1`) ánh xạ trực tiếp sang module Python khi import.
- Yêu cầu runtime/tooling:
  - Thêm `backend/src` hoặc `inference/src` vào `PYTHONPATH` (hoặc cài đặt project ở chế độ editable).
  - Khuyến nghị tạo `__init__.py` rỗng tại các cấp thư mục sinh ra (để IDE và công cụ tĩnh nhận diện đúng, dù PEP 420 cho phép namespace packages không có `__init__.py`).
- Không chỉnh sửa các file sinh ra; mọi thay đổi phải thực hiện trong `.proto` và sinh lại mã.

## 4. Tự động hóa với Makefile

Ví dụ target chuẩn hóa việc generate cho cả Backend và Inference (tham khảo, có thể điều chỉnh theo nhu cầu CI):

```make
# Makefile (trích đoạn)
PROTO_DIR := proto
BACKEND_OUT := backend/src
INFER_OUT := inference/src
PROTO_FILES := $(shell find $(PROTO_DIR) -name '*.proto')

.PHONY: proto-backend proto-inference proto-all

proto-backend:
	python -m grpc_tools.protoc -I $(PROTO_DIR) \
	  --python_out=$(BACKEND_OUT) --grpc_python_out=$(BACKEND_OUT) \
	  $(PROTO_FILES)

proto-inference:
	python -m grpc_tools.protoc -I $(PROTO_DIR) \
	  --python_out=$(INFER_OUT) --grpc_python_out=$(INFER_OUT) \
	  $(PROTO_FILES)

proto-all: proto-backend proto-inference
```

## 5. Hướng dẫn cấu hình JetBrains (PyCharm/IntelliJ/GoLand)

Nếu gặp lỗi kiểu `package ... must be within a directory ...` từ plugin Protobuf:
1. Mở `Settings/Preferences` → `Languages & Frameworks` → `Protocol Buffers`.
2. Import Paths:
   - Bỏ chọn `Include project content roots`.
   - Thêm đường dẫn tuyệt đối tới `proto/` của dự án.
3. Apply → OK.

## 6. Compatibility

- Backward compatibility:
  - Không thay đổi số trường (field numbers) của các trường hiện hữu.
  - Không xóa trường đang dùng; nếu ngừng sử dụng, đánh dấu bằng `reserved` (tên/số trường) để tránh tái sử dụng vô ý.
  - Thêm trường mới bằng số thứ tự chưa dùng.
- Breaking changes:
  - Tạo nhánh phiên bản mới (ví dụ `v2/`) và chuyển dịch vụ sang schema mới theo kế hoạch di trú.
- Quy trình:
  - Cập nhật `.proto` → sinh mã (Mục 2/4) → commit cả thay đổi ở `proto/` và mã sinh ra (nếu repo policy yêu cầu).
