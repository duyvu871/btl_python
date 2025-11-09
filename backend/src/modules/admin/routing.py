from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.database.models.user import User
from src.core.security.user import get_admin_user
from src.modules.user.schema import UserAdminCreate, UserAdminRead, UserListResponse, UserUpdate
from src.modules.user.use_cases import UserUseCase, get_user_usecase
from src.shared.schemas.response import SuccessResponse

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)],  # All routes require admin
)


@router.get("/users", response_model=SuccessResponse[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by email or username"),
    role: str | None = Query(None, description="Filter by role"),
    verified: bool | None = Query(None, description="Filter by verification status"),
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Get paginated list of all users with filtering options."""
    try:
        result = await user_usecase.list_users(page, page_size, search, role, verified)
        return SuccessResponse(data=UserListResponse(
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            users=[UserAdminRead.model_validate(user) for user in result["users"]],
        ))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}", response_model=SuccessResponse[UserAdminRead])
async def get_user(
    user_id: UUID,
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Get detailed information about a specific user."""
    try:
        user = await user_usecase.get_user_by_id(str(user_id))
        if not user:
            raise ValueError("User not found")
        return SuccessResponse(data=UserAdminRead.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/users/{user_id}", response_model=SuccessResponse[UserAdminRead])
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Update user information (admin only)."""
    try:
        user = await user_usecase.update_user(user_id, user_update, current_admin)
        return SuccessResponse(data=UserAdminRead.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Delete a user (admin only)."""
    try:
        await user_usecase.delete_user(user_id, current_admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats", response_model=SuccessResponse)
async def get_user_stats(
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Get user statistics for dashboard."""
    stats = await user_usecase.get_user_stats()
    return SuccessResponse(data=stats)


@router.post("/users/bulk-action", response_model=SuccessResponse)
async def bulk_action_users(
    user_ids: list[UUID],
    action: str = Query(..., description="Action to perform: verify, unverify, promote, demote, delete"),
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Perform bulk actions on multiple users."""
    try:
        result = await user_usecase.bulk_action_users(user_ids, action, current_admin)
        return SuccessResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users", response_model=SuccessResponse[UserAdminRead])
async def create_user(
    user_data: UserAdminCreate,
    user_usecase: UserUseCase = Depends(get_user_usecase),
    current_admin: User = Depends(get_admin_user),
):
    """Create a new user (admin only)."""
    try:
        user = await user_usecase.create_user(user_data)
        return SuccessResponse(data=UserAdminRead.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

