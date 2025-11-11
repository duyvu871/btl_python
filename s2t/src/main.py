"""
Inference Service Main Application

This is the main FastAPI application for the s2t service.
It uses the gRPC clients to communicate with various services.
"""
import asyncio
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from scalar_fastapi import Theme, get_scalar_api_reference
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.env import settings
from src.grpc import AuthGRPCClient, get_auth_client
from src.grpc.lifespan import lifespan_grpc_clients
from src.response import ErrorResponse, SuccessResponse
from .logger import logger
from .security import get_user_id


# ============================================
# Pydantic Models
# ============================================


class Word(BaseModel):
    """Model for a single word with timestamp"""
    word: str  # The word text
    start: float  # Start time in seconds
    end: float  # End time in seconds
    confidence: float  # Confidence score (0.0 to 1.0)


class TranscriptionSegment(BaseModel):
    """Model for a transcription segment with timestamp"""
    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str  # Transcribed text for this segment
    confidence: float  # Confidence score (0.0 to 1.0)
    words: list[Word]  # List of individual words with timestamps


class TranscribeRequest(BaseModel):
    """Request model for audio transcription"""
    uri: str  # URI of the audio file to be transcribed
    language: str = "en"  # Language code (e.g., "en", "vi")


class TranscribeResponse(BaseModel):
    """Response model for transcription result"""
    duration: float  # Total duration of the audio in seconds
    language: str  # Detected or specified language code
    segments: list[TranscriptionSegment]  # List of transcription segments with timestamps
    transcript: str  # Full transcribed text (concatenation of all segments)


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
async def validate_token_endpoint(
    request: TokenValidateRequest,
    client: AuthGRPCClient = Depends(get_auth_client),
):
    try:
        result = await client.validate_token(request.token)
        return SuccessResponse(data=TokenValidateResponse.model_validate(result))
    except ValueError as e:
        logger.debug(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post(f"{settings.API_PREFIX}/transcribe", response_model=SuccessResponse[TranscribeResponse])
async def transcribe_audio(
        request: TranscribeRequest,
        user_id: str = Depends(get_user_id),
):
    """
    Transcribe audio file from URI with token validation via auth gRPC service.

    Requires Authorization header with Bearer token, which will be validated
    against the auth gRPC service.

    Args:
        request: Transcription request with uri and language
        user_id: User ID extracted from token (injected by FastAPI)

    Returns:
        Transcription result with duration, segments, and full transcript

    Raises:
        HTTPException: If token is invalid or audio URI is not accessible
    """

    # Verify audio URI is accessible
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            head_response = await client.head(request.uri)
            if head_response.status_code >= 400:
                # Try GET if HEAD fails
                get_response = await client.get(request.uri, timeout=10.0)
                if get_response.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Audio URI not accessible: {request.uri}"
                    )
    except httpx.RequestError as e:
        logger.error(f"Failed to access audio URI {request.uri}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch audio from URI: {str(e)}"
        )

    # Simulate processing delay
    await asyncio.sleep(1.0)

    # Mock transcription result with multiple segments
    processing_time = time.time() - start_time

    # Create mock segments with word-level timestamps
    mock_segments = [
        TranscriptionSegment(
            start=0.0,
            end=2.5,
            text="This is the first segment of the transcription.",
            confidence=0.95,
            words=[
                Word(word="This", start=0.0, end=0.3, confidence=0.98),
                Word(word="is", start=0.3, end=0.5, confidence=0.96),
                Word(word="the", start=0.5, end=0.7, confidence=0.95),
                Word(word="first", start=0.7, end=1.1, confidence=0.94),
                Word(word="segment", start=1.1, end=1.6, confidence=0.93),
                Word(word="of", start=1.6, end=1.8, confidence=0.97),
                Word(word="the", start=1.8, end=2.0, confidence=0.96),
                Word(word="transcription.", start=2.0, end=2.5, confidence=0.95),
            ]
        ),
        TranscriptionSegment(
            start=2.5,
            end=5.8,
            text="Here is the second part with different content.",
            confidence=0.92,
            words=[
                Word(word="Here", start=2.5, end=2.8, confidence=0.94),
                Word(word="is", start=2.8, end=3.0, confidence=0.93),
                Word(word="the", start=3.0, end=3.2, confidence=0.91),
                Word(word="second", start=3.2, end=3.7, confidence=0.90),
                Word(word="part", start=3.7, end=4.1, confidence=0.92),
                Word(word="with", start=4.1, end=4.4, confidence=0.93),
                Word(word="different", start=4.4, end=5.0, confidence=0.89),
                Word(word="content.", start=5.0, end=5.8, confidence=0.91),
            ]
        ),
        TranscriptionSegment(
            start=5.8,
            end=9.2,
            text="And finally the last segment completes the audio.",
            confidence=0.97,
            words=[
                Word(word="And", start=5.8, end=6.1, confidence=0.98),
                Word(word="finally", start=6.1, end=6.6, confidence=0.96),
                Word(word="the", start=6.6, end=6.8, confidence=0.97),
                Word(word="last", start=6.8, end=7.2, confidence=0.98),
                Word(word="segment", start=7.2, end=7.7, confidence=0.96),
                Word(word="completes", start=7.7, end=8.4, confidence=0.95),
                Word(word="the", start=8.4, end=8.6, confidence=0.98),
                Word(word="audio.", start=8.6, end=9.2, confidence=0.97),
            ]
        ),
    ]

    # Build full transcript from segments
    full_transcript = " ".join(segment.text for segment in mock_segments)

    # Mock audio duration
    mock_duration = mock_segments[-1].end if mock_segments else 0.0

    logger.info(f"Transcription completed for URI {request.uri} in {processing_time:.2f}s (user: {user_id})")

    return SuccessResponse(data=TranscribeResponse(
        duration=mock_duration,
        language=request.language,
        segments=mock_segments,
        transcript=full_transcript
    ))


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
                except TimeoutError:
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
