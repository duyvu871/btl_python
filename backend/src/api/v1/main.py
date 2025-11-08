from fastapi import APIRouter
from src.modules.auth.routing import router as auth_router
from src.modules.admin.routing import router as admin_router
from src.modules.subscription.routing import router as subscription_router
from src.modules.record.routing import router as record_router

# Create main API router
api_router = APIRouter()

# Include the auth router
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(subscription_router)
api_router.include_router(record_router)
