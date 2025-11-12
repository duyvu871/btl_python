"""
Use case for checking if user has available quota.
"""
from uuid import UUID

from src.shared.uow import UnitOfWork


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
        # 1. Lấy subscription của user
        subscription = await self.uow.subscription_repo.get_active_subscription(user_id)

        # 2. Nếu không tìm thấy subscription
        if not subscription:
            return False, "Không tìm thấy gói đăng ký"

        # 3. Kiểm tra usage_count có vượt quá monthly_usage_limit không
        if subscription.usage_count >= subscription.plan_monthly_usage_limit_snapshot:
            return False, f"Đã đạt giới hạn {subscription.plan_monthly_usage_limit_snapshot} recordings/cycle"

        # 4. Kiểm tra used_seconds có vượt quá monthly_minutes * 60 không
        max_seconds = subscription.plan_monthly_minutes_snapshot * 60
        if subscription.used_seconds >= max_seconds:
            return False, f"Đã đạt giới hạn {subscription.plan_monthly_minutes_snapshot} phút/cycle"

        # 5. Nếu cả 2 điều kiện đều OK
        return True, ""
