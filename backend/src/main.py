import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from scalar_fastapi import Theme, get_scalar_api_reference
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

import src.core.logger
from src.api.v1.main import api_router
from src.core.config.env import env, global_logger_name
from src.shared.schemas.response import ErrorResponse
from src.modules.rag.ai.routing import lifespan

logger = logging.getLogger(global_logger_name)

app = FastAPI(
    title="Backend API",
    version="1.0.0",
    openapi_url=f"{env.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

if env.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=env.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "btl-python-backend",
        "version": "1.0.0"
    }

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

# Scalar UI endpoint
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title + " - Scalar UI",
        theme=Theme.BLUE_PLANET,
    )

# Include API routers here
app.include_router(api_router, prefix=env.API_PREFIX)
