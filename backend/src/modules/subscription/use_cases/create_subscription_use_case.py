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
        # TODO: Implement subscription creation logic
        #
        # HƯỚNG DẪN IMPLEMENT:
        # 1. Kiểm tra user đã có subscription chưa
        # 2. Lấy FREE plan (default plan)
        # 3. Tính toán cycle_start và cycle_end (chu kỳ 1 tháng)
        # 4. Tạo subscription với dữ liệu
        # 5. Trả về subscription đã tạo

        raise NotImplementedError("TODO: Implement create subscription logic")

