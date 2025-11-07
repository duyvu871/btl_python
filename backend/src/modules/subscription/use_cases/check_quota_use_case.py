"""
Use case for checking if user has available quota.
"""
from uuid import UUID

from fastapi import Depends

from src.shared.uow import UnitOfWork, get_uow


class CheckQuotaUseCase:
    """
    Use case for checking if a user has available quota to create a new recording.
    
    This is called before creating a recording to ensure the user hasn't exceeded
    their monthly usage limits or time limits.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID) -> tuple[bool, str]:
        """
        Kiểm tra xem user còn quota để tạo recording mới không.

        Args:
            user_id: User UUID
            
        Returns:
            Tuple of (has_quota: bool, error_message: str)
            Nếu has_quota = True, error_message = ""
            Nếu has_quota = False, error_message chứa lý do (VD: "Đã đạt giới hạn 10 recordings/tháng")
        """
        # TODO: Implement quota checking logic
        #
        # HƯỚNG DẪN IMPLEMENT:
        # 1. Lấy subscription của user
        # 2. Nếu không tìm thấy subscription
        # 3. Kiểm tra usage_count có vượt quá monthly_usage_limit không
        # 4. Kiểm tra used_seconds có vượt quá monthly_minutes * 60 không
        # 5. Nếu cả 2 điều kiện đều OK
        # GỢI Ý: Có thể dùng method has_quota() đã có sẵn trong repository

        raise NotImplementedError("TODO: Implement check quota logic")


def get_check_quota_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> CheckQuotaUseCase:
    """Dependency injector for CheckQuotaUseCase."""
    return CheckQuotaUseCase(uow)

