"""
Auth gRPC Client
"""
import logging
from typing import Optional

from grpc import aio

from speech_hub.auth.v1 import auth_service_pb2, auth_service_pb2_grpc
from src.env import settings
from src.grpc.base_client import BaseGRPCClient

# Configure logging
logger = logging.getLogger(__name__)


class AuthGRPCClient(BaseGRPCClient[auth_service_pb2_grpc.AuthServiceStub]):
    """
    gRPC client for Auth service.
    """

    def __init__(
            self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            timeout: Optional[float] = None,
            max_retries: Optional[int] = None,
            use_ssl: bool = False,
    ):
        """
        Initialize the Auth gRPC client.

        Args:
            host: gRPC server host (default: from settings)
            port: gRPC server port (default: from settings)
            timeout: Default timeout (default: from settings)
            max_retries: Max retry attempts (default: from settings)
            use_ssl: Whether to use SSL/TLS
        """
        super().__init__(
            host=host or settings.GRPC_AUTH_HOST,
            port=port or settings.GRPC_AUTH_PORT,
            timeout=timeout or settings.GRPC_AUTH_TIMEOUT,
            max_retries=max_retries or settings.GRPC_AUTH_MAX_RETRIES,
            use_ssl=use_ssl,
        )

    def create_stub(self, channel: aio.Channel) -> auth_service_pb2_grpc.AuthServiceStub:
        """
        Create the Auth service stub.
        """
        return auth_service_pb2_grpc.AuthServiceStub(channel)

    def get_service_name(self) -> str:
        """
        Get the service name.
        """
        return "Auth"

    async def validate_token(
            self,
            token: str,
            timeout: Optional[float] = None,
            use_retry: bool = True,
    ) -> dict:
        """
        Validate a JWT token.

        Args:
            token: The JWT token to validate
            timeout: Request timeout in seconds (uses default if None)
            use_retry: Whether to use retry logic

        Returns:
            dict with keys:
                - is_valid (bool): Whether the token is valid
                - user_id (str): User ID if token is valid
                - expires_at (int): Token expiration timestamp

        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        request = auth_service_pb2.ValidateTokenRequest(token=token)

        if use_retry and settings.GRPC_ENABLE_RETRY:
            response = await self.call_with_retry(
                self.get_stub().validate_token,
                request,
                timeout=timeout,
            )
        else:
            await self.ensure_connected()
            response = await self.get_stub().validate_token(
                request,
                timeout=timeout or self.timeout,
            )

        return {
            "is_valid": response.is_valid,
            "user_id": response.user_id,
            "expires_at": response.expires_at,
        }

    async def refresh_token(
            self,
            refresh_token: str,
            timeout: Optional[float] = None,
            use_retry: bool = True,
    ) -> dict:
        """
        Refresh a JWT token.

        Args:
            refresh_token: The refresh token
            timeout: Request timeout in seconds (uses default if None)
            use_retry: Whether to use retry logic

        Returns:
            dict with keys:
                - token (str): New access token
                - expires_at (int): Token expiration timestamp

        Raises:
            grpc.RpcError: If the gRPC call fails
        """
        request = auth_service_pb2.RefreshTokenRequest(refresh_token=refresh_token)

        if use_retry and settings.GRPC_ENABLE_RETRY:
            response = await self.call_with_retry(
                self.get_stub().refresh_token,
                request,
                timeout=timeout,
            )
        else:
            await self.ensure_connected()
            response = await self.get_stub().refresh_token(
                request,
                timeout=timeout or self.timeout,
            )

        return {
            "token": response.token,
            "expires_at": response.expires_at,
        }


# Singleton instance
_auth_client_instance: Optional[AuthGRPCClient] = None


async def get_auth_client() -> AuthGRPCClient:
    """
    FastAPI dependency to get the auth gRPC client.

    Usage:
        @app.get("/validate")
        async def validate_token(
            token: str,
            client: AuthGRPCClient = Depends(get_auth_client)
        ):
            result = await client.validate_token(token)
            return result
    """
    global _auth_client_instance
    if _auth_client_instance is None:
        _auth_client_instance = AuthGRPCClient.get_instance()
        await _auth_client_instance.connect()
    return _auth_client_instance


# Utility functions
async def validate_token_simple(token: str) -> dict:
    """
    Simple utility function to validate a token.

    Args:
        token: JWT token to validate

    Returns:
        dict with validation result
    """
    client = AuthGRPCClient.get_instance()
    async with client.session():
        return await client.validate_token(token)


async def refresh_token_simple(refresh_token: str) -> dict:
    """
    Simple utility function to refresh a token.

    Args:
        refresh_token: Refresh token

    Returns:
        dict with new token
    """
    client = AuthGRPCClient.get_instance()
    async with client.session():
        return await client.refresh_token(refresh_token)

