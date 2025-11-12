"""
Use case for creating a subscription when user registers.
"""
from uuid import UUID

from src.core.database.models.plan import BillingCycle
from src.core.database.models.user_subscription import UserSubscription
from src.shared.uow import UnitOfWork


class CreateSubscriptionUseCase:
    """
    Use case for creating a subscription for a new user.

    This is called during user registration to assign the default FREE plan
    to the new user.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID) -> UserSubscription:
        """
        Create a subscription with FREE plan for a new user.
        Ensures monthly cycle and sets snapshot via apply_plan_snapshot.
        """
        existing_subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        if existing_subscription:
            raise ValueError("User đã có subscription")

        free_plan = await self.uow.plan_repo.get_default_plan()
        if not free_plan:
            raise ValueError("Không tìm thấy FREE plan")

        # Luôn thiết lập cycle theo tháng khi tạo mới
        cycle_start, cycle_end = self.uow.subscription_repo.calculate_cycle_dates(BillingCycle.MONTHLY)

        # Tạo subscription trước với counters mặc định
        subscription = await self.uow.subscription_repo.create({
            "user_id": user_id,
            "plan_id": free_plan.id,
            "plan_code_snapshot": free_plan.code,
            "plan_name_snapshot": free_plan.name,
            "plan_monthly_minutes_snapshot": free_plan.monthly_minutes,
            "plan_monthly_usage_limit_snapshot": free_plan.monthly_usage_limit,
            "cycle_start": cycle_start,
            "cycle_end": cycle_end,
            "usage_count": 0,
            "used_seconds": 0,
        })

        await self.uow.session.flush()
        return subscription
