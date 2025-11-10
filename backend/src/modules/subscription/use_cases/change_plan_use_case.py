"""
Use case for changing user subscription plan.
"""
from uuid import UUID

from src.modules.subscription.schema import ChangePlanResponse, PlanResponse, SubscriptionResponse, UsageResponse
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
        prorate: bool = False
    ) -> ChangePlanResponse:
        """
        Change user's subscription plan.
        
        Args:
            user_id: User UUID
            plan_code: Target plan code (e.g., 'BASIC', 'PREMIUM')
            prorate: If True, reset usage counts when changing plan
            
        Returns:
            ChangePlanResponse with success message and updated subscription info
            
        Raises:
            ValueError: If plan not found or subscription not found
            
        Example:
        """
        # 1. Tìm plan mới theo code
        new_plan = await self.uow.plan_repo.get_by_code(plan_code)
        if not new_plan:
            raise ValueError(f"Plan với code '{plan_code}' không tồn tại")

        # 2. Lấy subscription hiện tại
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        if not subscription:
            raise ValueError("Không tìm thấy gói đăng ký")

        # 3. Cập nhật plan_id
        subscription.plan_id = new_plan.id
        # đổi cycle_start và cycle_end nếu cần thiết
        cycle_start, cycle_end = self.uow.subscription_repo.calculate_cycle_dates(new_plan.billing_cycle)
        subscription.cycle_start = cycle_start
        subscription.cycle_end = cycle_end

        # 4. Nếu prorate = True, reset usage về 0
        if prorate:
            subscription.usage_count = 0
            subscription.used_seconds = 0

        # Commit changes
        await self.uow.session.flush()

        # Reload subscription để lấy plan mới
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)

        # 5. Lấy usage stats mới
        usage_stats = await self.uow.subscription_repo.get_usage_stats(user_id)

        # 6. Trả về ChangePlanResponse
        plan_response = PlanResponse.model_validate(new_plan)
        usage_response = UsageResponse.model_validate(usage_stats)

        subscription_response = SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan=plan_response,
            cycle_start=subscription.cycle_start,
            cycle_end=subscription.cycle_end,
            usage=usage_response
        )

        message = f"Đã đổi gói đăng ký sang {new_plan.name}"
        if prorate:
            message += " và đã reset usage về 0"

        return ChangePlanResponse(
            message=message,
            new_plan=plan_response,
            subscription=subscription_response
        )


