from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from scalar_fastapi import get_scalar_api_reference, Theme
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from src.core.config.env import env
from src.shared.schemas.response import ErrorResponse
from src.api.v1.main import api_router
import src.core.logger

app = FastAPI(
    title="Backend API",
    version="1.0.0",
    openapi_url=f"{env.API_PREFIX}/openapi.json",
)

if env.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=env.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


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
