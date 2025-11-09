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
        # TODO: Implement subscription retrieval logic
        #
        # HƯỚNG DẪN IMPLEMENT:
        # 1. Lấy subscription hiện tại của user
        # 2. Nếu không tìm thấy, ném lỗi ValueError("Không tìm thấy gói đăng ký")
        # 3. Lấy usage statistics từ repository
        # 4. Convert Plan sang PlanResponse
        # 5. Convert usage_stats dict sang UsageResponse
        # 6. Trả về SubscriptionDetailResponse

        raise NotImplementedError("TODO: Implement get subscription logic")

