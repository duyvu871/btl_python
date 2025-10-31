import logging

from speech_hub.auth.v1.auth_service_pb2 import ValidateTokenRequest, ValidateTokenResponse, RefreshTokenRequest, \
    RefreshTokenResponse
from src.modules.user.repository import UserRepository
from speech_hub.auth.v1 import auth_service_pb2_grpc


class AuthGRPCService(auth_service_pb2_grpc.AuthServiceServicer):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def validate_token(self, request: ValidateTokenRequest, context):
        # Implement token validation logic here
        logging.info(f"AuthGRPCService validate_token {request}")
        return ValidateTokenResponse(is_valid=True, user_id="123", expires_at=1700000000)

    def refresh_token(self, request: RefreshTokenRequest, context):
        # Implement token refresh logic here
        logging.info(f"AuthGRPCService refresh_token {request}")
        return RefreshTokenResponse(token="123", expires_at=1700000000)