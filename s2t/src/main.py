"""
Inference Service Main Application

This is the main FastAPI application for the s2t service.
It uses the gRPC clients to communicate with various services.
"""
import asyncio
import logging

from fastapi import Depends, FastAPI, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from scalar_fastapi import get_scalar_api_reference, Theme

from src.env import settings
from src.grpc import AuthGRPCClient, get_auth_client
from src.grpc.lifespan import lifespan_grpc_clients
from src.response import ErrorResponse, SuccessResponse
from .logger import logger


# ============================================
# Pydantic Models
# ============================================

class TokenValidateRequest(BaseModel):
    token: str


class TokenValidateResponse(BaseModel):
    is_valid: bool
    user_id: str | None = None
    expires_at: int | None = None
    error: str | None = None


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

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title + " - Scalar UI",
        theme=Theme.BLUE_PLANET,
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
        "service": "Speech S2T Service",
        "environment": settings.ENVIRONMENT,
        "grpc_services": {
            "auth": auth_healthy,
        },
    }


# ============================================
# Auth Integration Endpoints
# ============================================

@app.post(f"{settings.API_PREFIX}/auth/validate", response_model=SuccessResponse[TokenValidateResponse])
async def validate_token(
    request: TokenValidateRequest,
    client: AuthGRPCClient = Depends(get_auth_client),
):
    try:
        result = await client.validate_token(request.token)
        return SuccessResponse(data=TokenValidateResponse(**result))
    except ValueError as e:
        logger.debug(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
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
            detail=f"Failed to refresh token",
        )


# ============================================
# WebSocket Endpoints
# ============================================

@app.websocket("/ws/s2t")
async def websocket_s2t(
    websocket: WebSocket,
    auth_client: AuthGRPCClient = Depends(get_auth_client),
):
    """
    WebSocket endpoint for real-time speech-to-text processing.

    Client should connect with token as query parameter: /ws/s2t?token=<jwt_token>

    Receives audio stream chunks and simulates S2T processing.
    """
    # Get token from query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    # Validate token
    try:
        validation_result = await auth_client.validate_token(token)
        if not validation_result["is_valid"]:
            await websocket.close(code=1008, reason="Invalid token")
            return
        user_id = validation_result["user_id"]
        logger.info(f"WebSocket S2T connection established for user {user_id}")
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        await websocket.close(code=1008, reason="Token validation failed")
        return

    # Accept the connection
    await websocket.accept()

    target_language = "en"  # Default
    try:
        # Receive initial message with target_language
        initial_message = await websocket.receive_json()
        target_language = initial_message.get("target_language", "en")
        logger.info(f"Target language set to {target_language} for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to receive initial message: {e}")

    try:
        while True:

            audio_buffer: list[bytes] = []
            start_time = asyncio.get_event_loop().time()

            while True:
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time >= 1.0: # 1 second of audio
                    break # out of inner loop

                remaining_time = 1.0 - elapsed_time

                try:
                    data = await asyncio.wait_for(
                        websocket.receive_bytes(),
                        remaining_time
                    )
                    audio_buffer.append(data)
                    logger.info(f"[{user_id}] WebSocket S2T connection received audio length: {len(data)}")
                except asyncio.TimeoutError:
                    break


            if audio_buffer:
                # Receive audio chunk
                combined_audio_chunk = b"".join(audio_buffer)
                logger.info(f"User {user_id}: Processing 500ms batch. Total size: {len(combined_audio_chunk)} bytes")

                # Simulate S2T processing (replace with actual processing)
                # For demo, just return a fake transcription
                transcription = "This is a simulated transcription of the audio chunk."

                # Send back the transcription as JSON
                await websocket.send_json({
                    "start_time": 0.0,  # Placeholder
                    "end_time": 1.0,    # Placeholder
                    "text": transcription
                })
            else:
                logger.debug(f"No audio received from user {user_id} in this interval")
                # No audio received in this interval, continue
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket S2T connection closed for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket S2T error for user {user_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")


# Register a global exception handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    catch HTTP exceptions and return JSON response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=str(exc.detail)
        ).model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions.
    """
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred."
        ).model_dump()
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
