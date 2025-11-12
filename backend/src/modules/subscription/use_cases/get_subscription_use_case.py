"""
Use case for getting user subscription details.
"""
from uuid import UUID

from src.modules.subscription.schema import PlanSnapshotResponse, SubscriptionDetailResponse, UsageResponse
from src.shared.uow import UnitOfWork


class GetSubscriptionUseCase:
    """Lấy chi tiết subscription + quota, dùng snapshot (an toàn khi plan bị xóa)."""

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
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        if not subscription:
            raise ValueError("Không tìm thấy gói đăng ký")

        usage_stats = await self.uow.subscription_repo.get_usage_stats(user_id)
        usage_response = UsageResponse.model_validate(usage_stats)

        plan_snapshot = PlanSnapshotResponse(
            code=subscription.plan_code_snapshot,
            name=subscription.plan_name_snapshot,
            monthly_minutes=subscription.plan_monthly_minutes_snapshot,
            monthly_usage_limit=subscription.plan_monthly_usage_limit_snapshot,
        )

        return SubscriptionDetailResponse(
            plan=plan_snapshot,
            cycle_start=subscription.cycle_start,
            cycle_end=subscription.cycle_end,
            usage=usage_response,
        )
