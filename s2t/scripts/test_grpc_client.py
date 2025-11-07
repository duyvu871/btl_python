import logging

import grpc

# 1. IMPORT CÁC FILE ĐƯỢC GEN RA
# Đường dẫn import này phụ thuộc vào cách bạn chạy protoc
# (Giả sử chúng nằm trong thư mục 'gen' và bạn chạy từ thư mục gốc)
from speech_hub.auth.v1 import auth_service_pb2, auth_service_pb2_grpc

# (Nếu bạn đã cài đặt nó như một package 'speech_hub_protos')
# from speech_hub.auth.v1 import auth_service_pb2
# from speech_hub.auth.v1 import auth_service_pb2_grpc

def run_client():
    # Địa chỉ và cổng của gRPC server
    server_address = 'localhost:50051'

    # 1. TẠO CHANNEL
    # Dùng insecure_channel cho ví dụ (không mã hóa SSL/TLS)
    # 'with' statement sẽ tự động đóng channel khi xong
    try:
        with grpc.insecure_channel(server_address) as channel:

            # 2. TẠO STUB
            # Stub này chứa các phương thức .validate_token() và .refresh_token()
            stub = auth_service_pb2_grpc.AuthServiceStub(channel)

            print(f"--- Đang kết nối đến {server_address} ---")

            # 3. CHUẨN BỊ REQUEST VÀ GỌI RPC

            # --- Ví dụ gọi validate_token ---
            token_to_validate = "my-secret-auth-token-123"
            print(f"Đang gọi validate_token với token: '{token_to_validate}'")

            # Tạo message request
            validate_req = auth_service_pb2.ValidateTokenRequest(
                token=token_to_validate
            )

            # Gọi RPC và nhận response
            validate_res = stub.validate_token(validate_req)

            print("--- Kết quả Validate ---")
            print(f"Token hợp lệ: {validate_res.is_valid}")
            print(f"User ID: {validate_res.user_id}")
            print(f"Hết hạn lúc: {validate_res.expires_at}")

            # --- Ví dụ gọi refresh_token ---
            refresh_token_to_use = "my-super-secret-refresh-token-xyz"
            print(f"\nĐang gọi refresh_token với token: '{refresh_token_to_use}'")

            refresh_req = auth_service_pb2.RefreshTokenRequest(
                refresh_token=refresh_token_to_use
            )

            refresh_res = stub.refresh_token(refresh_req)

            print("--- Kết quả Refresh ---")
            print(f"Token mới: {refresh_res.token}")
            print(f"Hết hạn lúc: {refresh_res.expires_at}")

    except grpc.RpcError as e:
        # Xử lý các lỗi phổ biến
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            logging.error(f"Không thể kết nối đến server tại {server_address}. Server có đang chạy không?")
        else:
            logging.error(f"Lỗi gRPC: {e.code()} - {e.details()}")
    except Exception as e:
        logging.error(f"Lỗi: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_client()
