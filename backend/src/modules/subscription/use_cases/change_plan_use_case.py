"""
Use case for changing user subscription plan.
"""
from uuid import UUID

from src.core.database.models.plan import BillingCycle
from src.modules.subscription.schema import (
    ChangePlanResponse,
    PlanSnapshotResponse,
    SubscriptionResponse,
    UsageResponse,
)
from src.shared.uow import UnitOfWork


class ChangePlanUseCase:
    """
    Use case for changing a user's subscription plan.

    This handles upgrading or downgrading between plans (e.g., FREE -> BASIC -> PREMIUM).
    Optionally can reset usage if prorate flag is set.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        plan_code: str,
        prorate: bool = False #
    ) -> ChangePlanResponse:
        """Change user's subscription plan.
        - apply_plan_snapshot(new_plan)
        - nếu prorate=True: reset counters + cycle theo tháng
        - nếu prorate=False: giữ nguyên cycle hiện tại
        """
        # 1. Tìm plan mới theo code
        new_plan = await self.uow.plan_repo.get_by_code(plan_code.upper())
        if not new_plan:
            raise ValueError(f"Plan with code ('{plan_code}') not found or inactive")

        # 2. Lấy subscription hiện tại
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        if not subscription:
            raise ValueError("Not found active subscription for user")

        # Cập nhật snapshot + plan_id
        subscription.apply_plan_snapshot(new_plan)

        if prorate:
            # Reset counters và đặt lại cycle về tháng hiện tại → tháng sau
            subscription.usage_count = 0
            subscription.used_seconds = 0
            cycle_start, cycle_end = self.uow.subscription_repo.calculate_cycle_dates(BillingCycle.MONTHLY)
            subscription.cycle_start = cycle_start
            subscription.cycle_end = cycle_end
        # nếu không prorate: giữ nguyên cycle_start/cycle_end hiện tại

        # Commit changes
        await self.uow.session.flush()

        # Response
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        usage_stats = await self.uow.subscription_repo.get_usage_stats(user_id)
        usage_response = UsageResponse.model_validate(usage_stats)

        plan_snapshot = PlanSnapshotResponse(
            code=subscription.plan_code_snapshot,
            name=subscription.plan_name_snapshot,
            monthly_minutes=subscription.plan_monthly_minutes_snapshot,
            monthly_usage_limit=subscription.plan_monthly_usage_limit_snapshot,
        )
        subscription_response = SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=plan_snapshot,
            cycle_start=subscription.cycle_start,
            cycle_end=subscription.cycle_end,
            usage=usage_response,
        )
        message = f"Changed subscription to {new_plan.name}"
        if prorate:
            message += " and reset usage to 0"
        return ChangePlanResponse(message=message, new_plan=plan_snapshot, subscription=subscription_response)
