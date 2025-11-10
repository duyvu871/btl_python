"""
Use case for creating a subscription when user registers.
"""
from uuid import UUID

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

        Args:
            user_id: User UUID

        Returns:
            Created UserSubscription instance

        Raises:
            ValueError: If FREE plan not found or subscription already exists

        """
        # 1. Kiểm tra user đã có subscription chưa
        existing_subscription = await self.uow.subscription_repo.get_active_subscription(user_id)
        if existing_subscription:
            raise ValueError("User đã có subscription")
        
        # 2. Lấy FREE plan (default plan)
        free_plan = await self.uow.plan_repo.get_default_plan()
        if not free_plan:
            raise ValueError("Không tìm thấy FREE plan")
        
        # 3. Tính toán cycle_start và cycle_end (chu kỳ 1 tháng)
        now = datetime.now(timezone.utc)
        cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Tính cycle_end: tháng sau, ngày 1
        if cycle_start.month == 12:
            cycle_end = cycle_start.replace(year=cycle_start.year + 1, month=1)
        else:
            cycle_end = cycle_start.replace(month=cycle_start.month + 1)
        
        # 4. Tạo subscription với dữ liệu
        subscription_data = {
            "user_id": user_id,
            "plan_id": free_plan.id,
            "cycle_start": cycle_start,
            "cycle_end": cycle_end,
            "usage_count": 0,
            "used_seconds": 0
        }
        
        subscription = await self.uow.subscription_repo.create(subscription_data)
        
        # 5. Trả về subscription đã tạo
        return subscription

