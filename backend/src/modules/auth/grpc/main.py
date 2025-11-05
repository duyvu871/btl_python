import logging
import grpc

from speech_hub.auth.v1.auth_service_pb2 import ValidateTokenRequest, ValidateTokenResponse, RefreshTokenRequest, \
    RefreshTokenResponse
from src.core.config.env import global_logger_name
from src.core.security.user import get_current_user
from src.modules.user.repository import UserRepository
from speech_hub.auth.v1 import auth_service_pb2_grpc

logger = logging.getLogger(global_logger_name)

class AuthGRPCService(auth_service_pb2_grpc.AuthServiceServicer):
    def __init__(self, session_factory):
        """
        Initialize the gRPC service with a session factory.

        Args:
            session_factory: Callable that creates new database sessions
        """
        self.session_factory = session_factory

    async def validate_token(self, request: ValidateTokenRequest, context):
        """
        Validate a JWT token.
        """
        async with self.session_factory() as session:
            try:
                user = await get_current_user(token=request.token, db=session)

                if user is None:
                    await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid credentials")

                logger.debug(f"Validate logic with session {session}...")

            except Exception as e:
                logger.error(f"Error login user: {e}")
                # Khi dùng 'grpc.aio', bạn nên dùng 'context.abort()'
                await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
        return ValidateTokenResponse(is_valid=True, user_id="123", expires_at=1700000000)

    async def refresh_token(self, request: RefreshTokenRequest, context):
        """
        Refresh a JWT token.
        """
        logging.info(f"AuthGRPCService refresh_token {request}")
        # TODO: Implement actual token refresh logic
        # For now, return a mock response
        return RefreshTokenResponse(token="123", expires_at=1700000000)