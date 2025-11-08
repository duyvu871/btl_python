"""
Helper class for subscription use cases.
Provides convenient wrappers around use cases with dependency injection support.
"""

from uuid import UUID

from fastapi import Depends

from src.modules.subscription.schema import SubscriptionDetailResponse, ChangePlanResponse
from src.modules.subscription.use_cases.get_subscription_use_case import GetSubscriptionUseCase
from src.modules.subscription.use_cases.change_plan_use_case import ChangePlanUseCase
from src.modules.subscription.use_cases.check_quota_use_case import CheckQuotaUseCase
from src.modules.subscription.use_cases.create_subscription_use_case import CreateSubscriptionUseCase
from src.core.database.models.user_subscription import UserSubscription
from src.shared.uow import UnitOfWork, get_uow


class SubscriptionUseCase:
    """
    Helper class that wraps subscription use cases.
    Designed to be used with FastAPI dependency injection.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize helper with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow
        self._get_subscription_use_case = GetSubscriptionUseCase(uow)
        self._change_plan_use_case = ChangePlanUseCase(uow)
        self._check_quota_use_case = CheckQuotaUseCase(uow)
        self._create_subscription_use_case = CreateSubscriptionUseCase(uow)

    async def get_subscription(self, user_id: UUID) -> SubscriptionDetailResponse:
        """
        Get subscription details for a user.
        """
        return await self._get_subscription_use_case.execute(user_id)

    async def change_plan(self, user_id: UUID, plan_code: str, prorate: bool = False) -> ChangePlanResponse:
        """
        Change user's subscription plan.
        """
        return await self._change_plan_use_case.execute(user_id, plan_code, prorate)

    async def check_quota(self, user_id: UUID) -> tuple[bool, str]:
        """
        Check if user has available quota.
        """
        return await self._check_quota_use_case.execute(user_id)

    async def create_subscription(self, user_id: UUID) -> UserSubscription:
        """
        Create a subscription for a new user.
        """
        return await self._create_subscription_use_case.execute(user_id)


def get_subscription_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> SubscriptionUseCase:
    """
    FastAPI dependency to get SubscriptionUseCase instance.

    Returns:
        SubscriptionUseCase instance
    """
    return SubscriptionUseCase(uow)
