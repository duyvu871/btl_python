"""
Base gRPC Client

This module provides an abstract base class for all gRPC clients in the application.
Each service-specific client should inherit from this base class.
"""
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Generic, Optional, TypeVar

import grpc
from grpc import aio
from src.env import settings

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for gRPC stub
TStub = TypeVar('TStub')


class BaseGRPCClient[TStub](ABC):
    """
    Abstract base class for gRPC clients.
    """

    _instance: Optional["BaseGRPCClient"] = None
    _channel: aio.Channel | None = None
    _stub: TStub | None = None

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 5.0,
        max_retries: int = 3,
        use_ssl: bool = False,
    ):
        """
        Initialize the gRPC client.

        Args:
            host: gRPC server host
            port: gRPC server port
            timeout: Default timeout for requests (seconds)
            max_retries: Maximum number of retry attempts
            use_ssl: Whether to use SSL/TLS
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_ssl = use_ssl
        self.address = f"{host}:{port}"

        logger.info(
            f"{self.get_service_name()} gRPC client initialized: "
            f"address={self.address}, timeout={timeout}s, ssl={use_ssl}"
        )

    @abstractmethod
    def create_stub(self, channel: aio.Channel) -> TStub:
        """
        Create the service-specific gRPC stub.

        Args:
            channel: gRPC channel

        Returns:
            Service-specific stub instance
        """
        pass

    @abstractmethod
    def get_service_name(self) -> str:
        """
        Get the service name for logging.

        Returns:
            Service name (e.g., "Auth", "Speech")
        """
        pass

    @classmethod
    def get_instance(cls, **kwargs) -> "BaseGRPCClient":
        """
        Get the singleton instance of the client.

        Args:
            **kwargs: Arguments to pass to __init__ (only used on first call)

        Returns:
            Client instance
        """
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """
        Reset the singleton instance
        """
        cls._instance = None
        cls._channel = None
        cls._stub = None

    async def connect(self):
        """
        Establish connection to the gRPC server.
        """
        if self._channel is None:
            logger.info(f"Connecting to {self.get_service_name()} gRPC server at {self.address}...")

            # Get gRPC channel options from settings
            options = settings.get_grpc_options()

            # Create channel
            if self.use_ssl:
                # TODO: Add SSL credentials
                credentials = grpc.ssl_channel_credentials()
                self._channel = aio.secure_channel(self.address, credentials, options=options)
            else:
                self._channel = aio.insecure_channel(self.address, options=options)

            # Create stub
            self._stub = self.create_stub(self._channel)

            logger.info(f"Successfully connected to {self.get_service_name()} gRPC server")

    async def disconnect(self):
        """
        Close the gRPC channel.
        """
        if self._channel is not None:
            logger.info(f"Closing {self.get_service_name()} gRPC connection...")
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info(f"{self.get_service_name()} gRPC connection closed")

    async def ensure_connected(self):
        """
        Ensure the client is connected to the gRPC server.
        """
        if self._channel is None or self._stub is None:
            await self.connect()

    @asynccontextmanager
    async def session(self):
        """
        Context manager for gRPC client session.

        Usage:
            async with client.session():
                result = await client.some_method()
        """
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    async def call_with_retry(
        self,
        method,
        request,
        timeout: float | None = None,
        max_retries: int | None = None,
    ):
        """
        Call a gRPC method with retry logic.

        Args:
            method: gRPC method to call
            request: Request message
            timeout: Request timeout (uses default if None)
            max_retries: Max retry attempts (uses default if None)

        Returns:
            Response from the gRPC method

        Raises:
            grpc.RpcError: If all retry attempts fail
        """
        await self.ensure_connected()

        timeout = timeout or self.timeout
        max_retries = max_retries or self.max_retries

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await method(request, timeout=timeout)
                return response
            except grpc.RpcError as e:
                last_error = e

                # Check if error is retryable
                if e.code() in [
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                ]:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{self.get_service_name()} gRPC call failed "
                            f"(attempt {attempt + 1}/{max_retries}): {e.code()} - {e.details()}"
                        )
                        continue

                # Non-retryable error or last attempt
                logger.error(
                    f"{self.get_service_name()} gRPC error: {e.code()} - {e.details()}"
                )
                raise

        # All retries exhausted
        if last_error:
            logger.error(
                f"{self.get_service_name()} gRPC call failed after {max_retries} attempts"
            )
            raise last_error
        return None

    async def health_check(self) -> bool:
        """
        Check if the gRPC server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.ensure_connected()
            return True
        except Exception as e:
            logger.error(f"{self.get_service_name()} health check failed: {e}")
            return False

    def get_stub(self) -> TStub:
        """
        Get the gRPC stub (ensure connected first).

        Returns:
            gRPC stub instance

        Raises:
            RuntimeError: If not connected
        """
        if self._stub is None:
            raise RuntimeError(
                f"{self.get_service_name()} gRPC client is not connected. "
                "Call ensure_connected() or connect() first."
            )
        return self._stub


class GRPCClientError(Exception):
    """Base exception for gRPC client errors."""
    pass


class GRPCConnectionError(GRPCClientError):
    """Exception for gRPC connection errors."""
    pass


class GRPCTimeoutError(GRPCClientError):
    """Exception for gRPC timeout errors."""
    pass


class GRPCUnavailableError(GRPCClientError):
    """Exception for gRPC unavailable errors."""
    pass

