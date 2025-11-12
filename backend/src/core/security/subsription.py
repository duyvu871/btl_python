import logging

from fastapi import Depends, HTTPException
from starlette import status

from src.core.config.env import global_logger_name
from src.core.database.models import User
from src.core.security.user import get_current_user
from src.modules.subscription.use_cases import SubscriptionUseCase, get_subscription_usecase

logger = logging.getLogger(global_logger_name)

async def get_subscription(
    current_user: User = Depends(get_current_user),
    use_case: SubscriptionUseCase = Depends(get_subscription_usecase),
):
    """
    Get current user's subscription details.

    Returns plan information, current cycle dates, and usage statistics.
    This is typically used for dashboard displays.

    Returns:
        SubscriptionDetailResponse with plan, cycle, and usage info
    """
    try:
        subscription = await use_case.get_subscription(current_user.id)
        return subscription
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Chức năng chưa được implement: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription details"
        )