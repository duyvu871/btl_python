"""
Use case for changing user subscription plan.
"""
from uuid import UUID

from fastapi import Depends

from src.modules.subscription.schema import ChangePlanResponse, PlanResponse, SubscriptionResponse, UsageResponse
from src.shared.uow import UnitOfWork, get_uow


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
        # TODO: Implement plan change logic
        #
        # HƯỚNG DẪN IMPLEMENT:
        # 1. Tìm plan mới theo code
        # 2. Lấy subscription hiện tại
        # 3. Cập nhật plan_id
        # 4. Nếu prorate = True, reset usage về 0
        # 5. Lấy usage stats mới
        # 6. Trả về ChangePlanResponse
        raise NotImplementedError("TODO: Implement change plan logic")


