"""
Environment Configuration for Inference Service

This module manages all environment variables and settings for the inference service.
"""
from functools import lru_cache
from typing import Optional, Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ============================================
    # API Settings
    # ============================================
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")

    # ============================================
    # CORS Settings
    # ============================================
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    # ============================================
    # gRPC Settings
    # ============================================

    # Auth gRPC Service
    GRPC_AUTH_HOST: str = Field(default="localhost", description="Auth gRPC server host")
    GRPC_AUTH_PORT: int = Field(default=50051, description="Auth gRPC server port")
    GRPC_AUTH_TIMEOUT: float = Field(default=5.0, description="Default timeout for Auth gRPC calls (seconds)")
    GRPC_AUTH_MAX_RETRIES: int = Field(default=3, description="Max retry attempts for Auth gRPC calls")

    # Additional gRPC Services
    GRPC_SPEECH_HOST: Optional[str] = Field(default=None, description="Speech gRPC server host")
    GRPC_SPEECH_PORT: Optional[int] = Field(default=None, description="Speech gRPC server port")
    GRPC_SPEECH_TIMEOUT: float = Field(default=30.0, description="Default timeout for Speech gRPC calls (seconds)")

    # gRPC Global Settings
    GRPC_ENABLE_RETRY: bool = Field(default=True, description="Enable retry for gRPC calls")
    GRPC_MAX_MESSAGE_LENGTH: int = Field(default=4 * 1024 * 1024, description="Max gRPC message size (4MB)")
    GRPC_KEEPALIVE_TIME_MS: int = Field(default=10000, description="Keepalive time in milliseconds")
    GRPC_KEEPALIVE_TIMEOUT_MS: int = Field(default=5000, description="Keepalive timeout in milliseconds")

    # ============================================
    # Logging Settings
    # ============================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    #
    # # ============================================
    # # Database Settings (if needed)
    # # ============================================
    # DATABASE_URL: Optional[str] = Field(default=None, description="Database connection URL")
    #
    # # ============================================
    # # Redis Settings (if needed)
    # # ============================================
    # REDIS_HOST: Optional[str] = Field(default=None, description="Redis host")
    # REDIS_PORT: Optional[int] = Field(default=6379, description="Redis port")
    # REDIS_DB: int = Field(default=0, description="Redis database number")
    # REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")

    # ============================================
    # Model Settings (for inference)
    # ============================================
    MODEL_PATH: Optional[str] = Field(default=None, description="Path to model files")
    MODEL_DEVICE: str = Field(default="cpu", description="Device to run models (cpu, cuda, mps)")
    MODEL_BATCH_SIZE: int = Field(default=1, description="Batch size for inference")

    # ============================================
    # Helper Properties
    # ============================================

    @property
    def grpc_auth_address(self) -> str:
        """Get full Auth gRPC server address"""
        return f"{self.GRPC_AUTH_HOST}:{self.GRPC_AUTH_PORT}"

    @property
    def grpc_speech_address(self) -> Optional[str]:
        """Get full Speech gRPC server address if configured"""
        if self.GRPC_SPEECH_HOST and self.GRPC_SPEECH_PORT:
            return f"{self.GRPC_SPEECH_HOST}:{self.GRPC_SPEECH_PORT}"
        return None

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"

    def get_grpc_options(self) -> list[tuple[str, any]]:
        """
        Get common gRPC channel options.

        Returns:
            List of gRPC channel options
        """
        return [
            ("grpc.max_send_message_length", self.GRPC_MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", self.GRPC_MAX_MESSAGE_LENGTH),
            ("grpc.keepalive_time_ms", self.GRPC_KEEPALIVE_TIME_MS),
            ("grpc.keepalive_timeout_ms", self.GRPC_KEEPALIVE_TIMEOUT_MS),
            ("grpc.keepalive_permit_without_calls", 1),
            ("grpc.http2.max_pings_without_data", 0),
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function uses lru_cache to ensure only one Settings instance is created.

    Returns:
        Settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()

