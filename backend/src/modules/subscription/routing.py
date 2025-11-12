"""
API routing for subscription module.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.config.env import global_logger_name
from src.core.database.models.user import User
from src.core.security.subsription import get_subscription
from src.core.security.user import get_current_user
from src.modules.subscription.schema import (
    ChangePlanRequest,
    ChangePlanResponse,
    PlanResponse,
    QuotaCheckResponse,
    SubscriptionDetailResponse,
)
from src.modules.subscription.use_cases.helpers import SubscriptionUseCase, get_subscription_usecase
from src.shared.schemas.response import SuccessResponse
from src.shared.uow import UnitOfWork, get_uow

logger = logging.getLogger(global_logger_name)

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)


@router.get("/me", response_model=SuccessResponse[SubscriptionDetailResponse])
async def get_my_subscription(
    subscription: SubscriptionDetailResponse = Depends(get_subscription)
):
    """
    Get current user's subscription details.

    Returns plan information, current cycle dates, and usage statistics.
    This is typically used for dashboard displays.

    Returns:
        SubscriptionDetailResponse with plan, cycle, and usage info
    """
    try:
        return SuccessResponse(data=subscription)
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription details"
        )


@router.get("/check-quota", response_model=SuccessResponse[QuotaCheckResponse])
async def check_quota(
    current_user: User = Depends(get_current_user),
    use_case: SubscriptionUseCase = Depends(get_subscription_usecase),
):
    """
    Check if current user has available quota.

    This endpoint is useful for frontend to check before allowing
    user to start a recording.

    Returns:
        QuotaCheckResponse with has_quota flag and error message if no quota
    """
    try:
        has_quota, error_msg = await use_case.check_quota(current_user.id)
        return SuccessResponse(
            data=QuotaCheckResponse(
                has_quota=has_quota,
                error_message=error_msg
            )
        )
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Chức năng chưa được implement: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error checking quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check quota"
        )


@router.post("/change-plan", response_model=SuccessResponse[ChangePlanResponse])
async def change_plan(
    request: ChangePlanRequest,
    current_user: User = Depends(get_current_user),
    use_case: SubscriptionUseCase = Depends(get_subscription_usecase),
):
    """
    Change user's subscription plan.

    Allows upgrading or downgrading to a different plan.
    If prorate=True, usage will be reset immediately.

    Args:
        request: ChangePlanRequest with plan_code and prorate flag
        current_user: Authenticated user
        use_case: SubscriptionUseCase instance
    Returns:
        ChangePlanResponse with success message and updated subscription
    """
    try:
        result = await use_case.change_plan(
            current_user.id,
            request.plan_code,
            request.prorate
        )
        return SuccessResponse(data=result)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Chức năng chưa được implement: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error changing plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change plan"
        )


@router.get("/plans", response_model=SuccessResponse[list[PlanResponse]])
async def list_plans(
    uow: UnitOfWork = Depends(get_uow),
):
    """
    List all available subscription plans.

    This is a public endpoint that shows all active plans
    that users can subscribe to.

    Returns:
        List of PlanResponse objects
    """
    try:
        plans = await uow.plan_repo.list_active_plans()
        plan_responses = [PlanResponse.model_validate(plan) for plan in plans]
        return SuccessResponse(data=plan_responses)
    except Exception as e:
        logger.error(f"Error listing plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans"
        )
