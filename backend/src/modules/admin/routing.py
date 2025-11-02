from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.db import get_db
from src.core.security.user import get_admin_user
from src.modules.user.schema import UserListResponse

# from src.core.database.database import get_db
# from src.core.database.models.user import User
# from src.core.security import get_admin_user
# from src.domains.admin.use_cases import AdminUseCase, get_admin_usecase
# from src.schemas.user import UserAdminCreate, UserAdminRead, UserListResponse, UserUpdate

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)],  # All routes require admin
)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by email or username"),
    role: str | None = Query(None, description="Filter by role"),
    verified: bool | None = Query(None, description="Filter by verification status"),
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Get paginated list of all users with filtering options."""
    try:
        result = await admin_use_case.list_users(db, page, page_size, search, role, verified)
        return UserListResponse(
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            users=[UserAdminRead.model_validate(user) for user in result["users"]],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}", response_model=UserAdminRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Get detailed information about a specific user."""
    try:
        user = await admin_use_case.get_user(db, user_id)
        return UserAdminRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/users/{user_id}", response_model=UserAdminRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Update user information (admin only)."""
    try:
        user = await admin_use_case.update_user(db, user_id, user_update, current_admin)
        return UserAdminRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Delete a user (admin only)."""
    try:
        await admin_use_case.delete_user(db, user_id, current_admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Get user statistics for dashboard."""
    return await admin_use_case.get_user_stats(db)


@router.post("/users/bulk-action")
async def bulk_action_users(
    user_ids: list[UUID],
    action: str = Query(..., description="Action to perform: verify, unverify, promote, demote, delete"),
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Perform bulk actions on multiple users."""
    try:
        return await admin_use_case.bulk_action_users(db, user_ids, action, current_admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users", response_model=UserAdminRead)
async def create_user(
    user_data: UserAdminCreate,
    db: AsyncSession = Depends(get_db),
    admin_use_case: AdminUseCase = Depends(get_admin_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Create a new user (admin only)."""
    try:
        user = await admin_use_case.create_user(db, user_data)
        return UserAdminRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
