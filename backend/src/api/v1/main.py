from fastapi import APIRouter
from src.modules.auth.routing import router as auth_router

# Create main API router
api_router = APIRouter()

# Include the auth router
api_router.include_router(auth_router)