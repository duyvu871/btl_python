"""
Use case for getting user subscription details.
"""
from uuid import UUID

from src.modules.subscription.schema import SubscriptionDetailResponse
from src.shared.uow import UnitOfWork


class GetSubscriptionUseCase:
    """
    Use case for retrieving user subscription details.

    This is typically used for dashboard displays where users can see their
    current plan, usage statistics, and remaining quota.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID) -> SubscriptionDetailResponse:
        """
        Get subscription details including plan info and usage stats.

        Args:
            user_id: User UUID

        Returns:
            SubscriptionDetailResponse with plan, cycle dates, and usage statistics

        Raises:
            ValueError: If no active subscription found

        Example response:
            {
                "plan": {
                    "code": "FREE",
                    "name": "Free Plan",
                    "monthly_minutes": 30,
                    "monthly_usage_limit": 10
                },
                "cycle_start": "2025-11-01T00:00:00Z",
                "cycle_end": "2025-12-01T00:00:00Z",
                "usage": {
                    "usage_count": 3,
                    "remaining_count": 7,
                    "used_minutes": 7.5,
                    "remaining_minutes": 22.5
                }
            }
        """
        # 1. Lấy subscription hiện tại của user
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        
        # 2. Nếu không tìm thấy, ném lỗi ValueError("Không tìm thấy gói đăng ký")
        if not subscription:
            raise ValueError("Không tìm thấy gói đăng ký")
        
        # 3. Lấy usage statistics từ repository
        usage_stats = await self.uow.subscription_repo.get_usage_stats(user_id)
        
        # 4. Convert Plan sang PlanResponse
        plan_response = PlanResponse.model_validate(subscription.plan)
        
        # 5. Convert usage_stats dict sang UsageResponse
        usage_response = UsageResponse.model_validate(usage_stats)
        
        # 6. Trả về SubscriptionDetailResponse
        return SubscriptionDetailResponse(
            plan=plan_response,
            cycle_start=subscription.cycle_start,
            cycle_end=subscription.cycle_end,
            usage=usage_response
        )

