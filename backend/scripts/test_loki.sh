#!/bin/bash

# 1. Lấy timestamp hiện tại (tính bằng giây) và thêm "000000000"
#    (Cách này an toàn, hoạt động trên cả Linux và macOS)
TS_NANO=$(date +%s)"000000000"

# 2. Tạo nội dung JSON (payload)
#    (Dùng `printf` là cách an toàn để chèn biến $TS_NANO vào)
PAYLOAD=$(printf '{
  "streams": [
    {
      "stream": {
        "source": "bash-dynamic-test",
        "level": "info"
      },
      "values": [
        [ "%s", "Log test tu dong tu BASH voi timestamp chinh xac." ]
      ]
    }
  ]
}' "$TS_NANO")

# 3. Gửi request bằng curl
echo "--- Dang gui log voi timestamp: $TS_NANO ---"

curl -v -X POST -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "http://localhost:7100/loki/api/v1/push"

echo "------------------------------------------------"
