"""
Inference Service Main Application

This is the main FastAPI application for the s2t service.
It uses the gRPC clients to communicate with various services.
"""
import logging

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.env import settings
from src.grpc import AuthGRPCClient, get_auth_client
from src.grpc.lifespan import lifespan_grpc_clients

logger = logging.getLogger(__name__)


# ============================================
# Pydantic Models
# ============================================

class TokenValidateRequest(BaseModel):
    token: str


class TokenValidateResponse(BaseModel):
    is_valid: bool
    user_id: str | None = None
    expires_at: int | None = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    token: str
    expires_at: int


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    grpc_services: dict[str, bool]


# ============================================
# Create FastAPI App
# ============================================

app = FastAPI(
    title="Speech S2T Service",
    description="Speech s2t service with gRPC integration",
    version="1.0.0",
    lifespan=lifespan_grpc_clients,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

if settings.CORS_ORIGINS:
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ============================================
# Health Check Endpoints
# ============================================

@app.get("/", response_model=HealthResponse)
async def root(auth_client: AuthGRPCClient = Depends(get_auth_client)):
    """Root endpoint - health check"""
    # Check gRPC services health
    auth_healthy = await auth_client.health_check()

    return {
        "status": "healthy" if auth_healthy else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "grpc_services": {
            "auth": auth_healthy,
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(auth_client: AuthGRPCClient = Depends(get_auth_client)):
    """
    Detailed health check endpoint that verifies all gRPC connections.
    """
    auth_healthy = await auth_client.health_check()

    overall_status = "healthy" if auth_healthy else "degraded"

    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "grpc_services": {
            "auth": auth_healthy,
        },
    }


# ============================================
# Auth Integration Endpoints
# ============================================

@app.post(f"{settings.API_PREFIX}/auth/validate", response_model=TokenValidateResponse)
async def validate_token(
    request: TokenValidateRequest,
    client: AuthGRPCClient = Depends(get_auth_client),
):
    try:
        result = await client.validate_token(request.token)
        return TokenValidateResponse(**result)
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate token: {str(e)}",
        )


@app.post(f"{settings.API_PREFIX}/auth/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    client: AuthGRPCClient = Depends(get_auth_client),
):
    """
    Refresh a JWT token using the Auth gRPC service.

    Args:
        request: Token refresh request
        client: Injected Auth gRPC client

    Returns:
        New access token

    Raises:
        HTTPException: If refresh fails or gRPC error occurs
    """
    try:
        result = await client.refresh_token(request.refresh_token)
        return TokenRefreshResponse(**result)
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh token: {str(e)}",
        )





# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Log startup message"""
    logger.info("=" * 60)
    logger.info(f"{settings.APP_NAME} Started")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown message"""
    logger.info(f"{settings.APP_NAME} Shutting Down")

