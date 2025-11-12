from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.core.database.models.user import User
from src.core.security.user import get_admin_user
from src.modules.subscription.schema import PlanResponse, SubscriptionDetailResponse
from src.modules.user.schema import UserAdminCreate, UserAdminRead, UserListResponse, UserUpdate
from src.modules.user.use_cases import UserUseCase, get_user_usecase
from src.shared.schemas.response import SuccessResponse
from src.shared.uow import UnitOfWork, get_uow

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)],  # All routes require admin
)

# ============================================================================
# Subscription Admin Schemas
# ============================================================================

class PlanCreateRequest(BaseModel):
    code: str = Field(..., description="Plan code (uppercase)")
    name: str
    description: str | None = None
    plan_type: str
    billing_cycle: str = "MONTHLY"
    plan_cost: int = 0
    plan_discount: int = 0
    monthly_minutes: int
    monthly_usage_limit: int
    is_default: bool = False
    is_active: bool = True


class PlanUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    plan_cost: int | None = None
    plan_discount: int | None = None
    monthly_minutes: int | None = None
    monthly_usage_limit: int | None = None
    is_active: bool | None = None


class SubscriptionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    subscriptions: list[dict]


class PlanStatsResponse(BaseModel):
    total_plans: int
    active_plans: int
    inactive_plans: int
    total_subscriptions: int
    subscriptions_by_plan: dict[str, int]


class MigrateSubscriptionsRequest(BaseModel):
    from_plan_code: str
    to_plan_code: str
    reset_usage: bool = False


# ============================================================================
# User Management Endpoints
# ============================================================================

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

# ============================================================================
# Subscription & Plan Management Endpoints
# ============================================================================

@router.get("/plans", response_model=SuccessResponse[list[PlanResponse]])
async def list_all_plans(
    include_inactive: bool = Query(False, description="Include inactive plans"),
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """List all plans (including inactive if specified)."""
    from sqlalchemy import select

    from src.core.database.models.plan import Plan

    if include_inactive:
        result = await uow.session.execute(select(Plan).order_by(Plan.plan_cost))
        plans = result.scalars().all()
    else:
        plans = await uow.plan_repo.list_active_plans()

    return SuccessResponse(data=[PlanResponse.model_validate(p) for p in plans])


@router.post("/plans", response_model=SuccessResponse[PlanResponse])
async def create_plan(
    data: PlanCreateRequest,
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Create a new plan."""
    from src.core.database.models.plan import BillingCycle, Plan, PlanType

    # Check if code already exists
    existing = await uow.plan_repo.get_by_code(data.code.upper())
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan code already exists")

    # If setting as default, ensure only one default exists
    if data.is_default:
        from sqlalchemy import update
        await uow.session.execute(
            update(Plan).where(Plan.is_default.is_(True)).values(is_default=False)
        )

    plan = Plan(
        code=data.code.upper(),
        name=data.name,
        description=data.description,
        plan_type=PlanType[data.plan_type],
        billing_cycle=BillingCycle[data.billing_cycle],
        plan_cost=data.plan_cost,
        plan_discount=data.plan_discount,
        monthly_minutes=data.monthly_minutes,
        monthly_usage_limit=data.monthly_usage_limit,
        is_default=data.is_default,
        is_active=data.is_active,
    )
    uow.session.add(plan)
    await uow.session.commit()
    await uow.session.refresh(plan)

    return SuccessResponse(data=PlanResponse.model_validate(plan))


@router.patch("/plans/{plan_id}", response_model=SuccessResponse[PlanResponse])
async def update_plan(
    plan_id: UUID,
    data: PlanUpdateRequest,
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Update plan details."""
    from sqlalchemy import select

    from src.core.database.models.plan import Plan

    result = await uow.session.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalars().first()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if plan.is_default and data.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate default plan")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await uow.session.commit()
    await uow.session.refresh(plan)

    return SuccessResponse(data=PlanResponse.model_validate(plan))


@router.post("/plans/{plan_id}/deactivate", response_model=SuccessResponse)
async def deactivate_plan(
    plan_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Deactivate a plan (soft delete)."""
    try:
        await uow.plan_repo.deactivate_plan(plan_id)
        await uow.session.commit()
        return SuccessResponse(data={"message": "Plan deactivated successfully"})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/subscriptions", response_model=SuccessResponse[SubscriptionListResponse])
async def list_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    plan_code: str | None = Query(None, description="Filter by plan code"),
    user_email: str | None = Query(None, description="Filter by user email"),
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """List all user subscriptions with pagination."""
    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload

    from src.core.database.models.user import User as UserModel
    from src.core.database.models.user_subscription import UserSubscription

    query = select(UserSubscription).options(selectinload(UserSubscription.plan), selectinload(UserSubscription.user))

    # Apply filters
    if plan_code:
        query = query.where(UserSubscription.plan_code_snapshot == plan_code.upper())
    if user_email:
        query = query.join(UserModel).where(UserModel.email.ilike(f"%{user_email}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await uow.session.execute(count_query)).scalar()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await uow.session.execute(query)
    subscriptions = result.scalars().all()

    subs_data = []
    for sub in subscriptions:
        subs_data.append({
            "id": str(sub.id),
            "user_id": str(sub.user_id),
            "user_email": sub.user.email if sub.user else None,
            "plan_code": sub.plan_code_snapshot,
            "plan_name": sub.plan_name_snapshot,
            "cycle_start": sub.cycle_start.isoformat(),
            "cycle_end": sub.cycle_end.isoformat(),
            "usage_count": sub.usage_count,
            "used_seconds": sub.used_seconds,
            "monthly_usage_limit": sub.plan_monthly_usage_limit_snapshot,
            "monthly_minutes": sub.plan_monthly_minutes_snapshot,
        })

    return SuccessResponse(data=SubscriptionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        subscriptions=subs_data,
    ))


@router.get("/subscriptions/{user_id}", response_model=SuccessResponse[SubscriptionDetailResponse])
async def get_user_subscription(
    user_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Get subscription details for a specific user."""
    from src.modules.subscription.use_cases import GetSubscriptionUseCase

    use_case = GetSubscriptionUseCase(uow)
    try:
        subscription = await use_case.execute(user_id)
        return SuccessResponse(data=subscription)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/subscriptions/{user_id}/change-plan", response_model=SuccessResponse)
async def admin_change_user_plan(
    user_id: UUID,
    plan_code: str = Query(..., description="Target plan code"),
    prorate: bool = Query(False, description="Reset usage"),
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Admin: change a user's subscription plan."""
    from src.modules.subscription.use_cases import ChangePlanUseCase

    use_case = ChangePlanUseCase(uow)
    try:
        result = await use_case.execute(user_id, plan_code, prorate)
        await uow.session.commit()
        return SuccessResponse(data={"message": f"Changed user plan to {plan_code}", "subscription": result})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/subscriptions/migrate", response_model=SuccessResponse)
async def migrate_subscriptions(
    data: MigrateSubscriptionsRequest,
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Bulk migrate subscriptions from one plan to another."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from src.core.database.models.user_subscription import UserSubscription

    # Get target plan
    to_plan = await uow.plan_repo.get_by_code(data.to_plan_code.upper())
    if not to_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target plan not found")

    # Find subscriptions on old plan
    query = select(UserSubscription).options(selectinload(UserSubscription.plan)).where(
        UserSubscription.plan_code_snapshot == data.from_plan_code.upper()
    )
    result = await uow.session.execute(query)
    subscriptions = result.scalars().all()

    migrated_count = 0
    for sub in subscriptions:
        sub.apply_plan_snapshot(to_plan)
        if data.reset_usage:
            sub.usage_count = 0
            sub.used_seconds = 0
        migrated_count += 1

    await uow.session.commit()

    return SuccessResponse(data={
        "message": f"Migrated {migrated_count} subscriptions from {data.from_plan_code} to {data.to_plan_code}",
        "migrated_count": migrated_count,
    })


@router.get("/subscription-stats", response_model=SuccessResponse[PlanStatsResponse])
async def get_subscription_stats(
    uow: UnitOfWork = Depends(get_uow),
    current_admin: User = Depends(get_admin_user),
):
    """Get subscription and plan statistics."""
    from sqlalchemy import func, select

    from src.core.database.models.plan import Plan
    from src.core.database.models.user_subscription import UserSubscription

    # Count plans
    total_plans = (await uow.session.execute(select(func.count()).select_from(Plan))).scalar()
    active_plans = (await uow.session.execute(select(func.count()).select_from(Plan).where(Plan.is_active.is_(True)))).scalar()
    inactive_plans = total_plans - active_plans

    # Count total subscriptions
    total_subs = (await uow.session.execute(select(func.count()).select_from(UserSubscription))).scalar()

    # Subscriptions by plan
    subs_by_plan = {}
    query = select(UserSubscription.plan_code_snapshot, func.count()).group_by(UserSubscription.plan_code_snapshot)
    result = await uow.session.execute(query)
    for code, count in result:
        subs_by_plan[code] = count

    return SuccessResponse(data=PlanStatsResponse(
        total_plans=total_plans,
        active_plans=active_plans,
        inactive_plans=inactive_plans,
        total_subscriptions=total_subs,
        subscriptions_by_plan=subs_by_plan,
    ))
