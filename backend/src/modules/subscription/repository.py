"""
Repository layer for subscription module.
Handles database queries for Plan and UserSubscription models.
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models.plan import BillingCycle, Plan, PlanType
from src.core.database.models.user_subscription import UserSubscription
from src.shared.base.base_repository import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    """
    Repository for Plan model.
    Manages CRUD operations and business queries for subscription plans.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Plan, session)

    async def get_by_code(self, code: str) -> Plan | None:
        """Lấy plan theo code (uppercase), chỉ trả về nếu active hoặc default."""
        normalized = code.upper()
        result = await self.session.execute(select(Plan).where(Plan.code == normalized))
        plan = result.scalars().first()
        if plan and (plan.is_active or plan.is_default):
            return plan
        return None

    async def list_active_plans(self) -> list[Plan]:
        """Danh sách plan đang active."""
        result = await self.session.execute(
            select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.plan_cost)
        )
        return list(result.scalars().all())

    async def get_default_plan(self) -> Plan | None:
        """Lấy default plan (is_default = True)."""
        result = await self.session.execute(select(Plan).where(Plan.is_default.is_(True)))
        return result.scalars().first()

    async def deactivate_plan(self, plan_id: UUID) -> None:
        """Soft deactivate plan (is_active=False), chặn nếu là default."""
        result = await self.session.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalars().first()
        if not plan:
            return
        if plan.is_default:
            raise ValueError("Không thể deactivate default plan")
        plan.is_active = False
        await self.session.flush()

    async def get_by_type(self, plan_type: PlanType) -> Plan | None:
        """
        Get plan by type.

        Args:
            plan_type: PlanType enum value

        Returns:
            Plan instance or None
        """
        query = select(Plan).where(Plan.plan_type == plan_type)
        result = await self.session.execute(query)
        return result.scalars().first()


class SubscriptionRepository(BaseRepository[UserSubscription]):
    """
    Repository for UserSubscription model.
    Manages user subscriptions and quota tracking.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(UserSubscription, session)

    def calculate_cycle_dates(self, billing_cycle: BillingCycle) -> tuple[datetime, datetime]:
        """
        Calculate cycle_start and cycle_end based on billing_cycle.

        Args:
            billing_cycle: The billing cycle type

        Returns:
            Tuple of (cycle_start, cycle_end)
        """
        from datetime import datetime, timezone

        now = datetime.now(UTC)
        if billing_cycle == BillingCycle.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(
                month=start.month + 1)
        elif billing_cycle == BillingCycle.YEARLY:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        elif billing_cycle == BillingCycle.LIFETIME:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 100)
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(
                month=start.month + 1)
        return start, end

    async def get_active_subscription(self, user_id: UUID) -> UserSubscription | None:
        """
        Get the active subscription for a user.
        Loads the related plan data.

        Args:
            user_id: User UUID

        Returns:
            UserSubscription instance with plan loaded, or None
        """
        query = (
            select(UserSubscription)
            .options(selectinload(UserSubscription.plan))
            .where(UserSubscription.user_id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def has_quota(self, user_id: UUID) -> tuple[bool, str]:
        """Kiểm tra quota dựa trên snapshot fields (an toàn khi plan bị xóa)."""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return False, "No active subscription found"
        if subscription.usage_count >= subscription.plan_monthly_usage_limit_snapshot:
            return False, f"Monthly usage limit reached ({subscription.plan_monthly_usage_limit_snapshot} recordings)"
        max_seconds = subscription.plan_monthly_minutes_snapshot * 60
        if subscription.used_seconds >= max_seconds:
            return False, f"Monthly time limit reached ({subscription.plan_monthly_minutes_snapshot} minutes)"
        return True, ""

    async def increment_usage(self, user_id: UUID) -> None:
        """
        Increment usage count for a user's subscription.
        This is typically called when a new recording is created.

        Args:
            user_id: User UUID
        """
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return
        subscription.usage_count += 1
        await self.session.flush()

    async def update_used_seconds(self, user_id: UUID, seconds: int) -> None:
        """
        Update the total used seconds for a user's subscription.
        This is called when a recording is completed.

        Args:
            user_id: User UUID
            seconds: Number of seconds to add to used_seconds
        """
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return
        subscription.used_seconds += seconds
        await self.session.flush()

    async def get_usage_stats(self, user_id: UUID) -> dict:
        """Trả về thống kê sử dụng dựa trên snapshot quota."""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return {
                'usage_count': 0,
                'monthly_usage_limit': 0,
                'remaining_count': 0,
                'used_seconds': 0,
                'monthly_seconds': 0,
                'remaining_seconds': 0,
                'used_minutes': 0.0,
                'monthly_minutes': 0,
                'remaining_minutes': 0.0
            }
        monthly_seconds = subscription.plan_monthly_minutes_snapshot * 60
        remaining_seconds = max(0, monthly_seconds - subscription.used_seconds)
        remaining_count = max(0, subscription.plan_monthly_usage_limit_snapshot - subscription.usage_count)
        return {
            'usage_count': subscription.usage_count,
            'monthly_usage_limit': subscription.plan_monthly_usage_limit_snapshot,
            'remaining_count': remaining_count,
            'used_seconds': subscription.used_seconds,
            'monthly_seconds': monthly_seconds,
            'remaining_seconds': remaining_seconds,
            'used_minutes': round(subscription.used_seconds / 60, 2),
            'monthly_minutes': subscription.plan_monthly_minutes_snapshot,
            'remaining_minutes': round(remaining_seconds / 60, 2)
        }

    async def reset_cycle(self, user_id: UUID) -> None:
        """Reset cycle + fallback về default plan nếu plan bị xóa/inactive."""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return
        # Lifetime: nếu có plan và là LIFETIME thì không reset
        if subscription.plan and subscription.plan.billing_cycle == BillingCycle.LIFETIME:
            return
        subscription.usage_count = 0
        subscription.used_seconds = 0
        # Tính ngày mới dựa trên plan nếu còn active, nếu không default monthly
        billing_cycle = subscription.plan.billing_cycle if subscription.plan else BillingCycle.MONTHLY
        start, end = self.calculate_cycle_dates(billing_cycle)
        subscription.cycle_start = start
        subscription.cycle_end = end
        # Fallback nếu plan None hoặc inactive
        if (not subscription.plan) or (subscription.plan and not subscription.plan.is_active):
            default_result = await self.session.execute(select(Plan).where(Plan.is_default.is_(True)))
            default_plan = default_result.scalars().first()
            if default_plan:
                subscription.apply_plan_snapshot(default_plan)
        await self.session.flush()

    async def migrate_all_inactive_to_default(self) -> int:
        """Bulk migrate subscriptions có plan bị xóa/inactive về default plan."""
        default_result = await self.session.execute(select(Plan).where(Plan.is_default.is_(True)))
        default_plan = default_result.scalars().first()
        if not default_plan:
            return 0
        result = await self.session.execute(select(UserSubscription).options(selectinload(UserSubscription.plan)))
        migrated = 0
        for sub in result.scalars().all():
            if (not sub.plan) or (sub.plan and not sub.plan.is_active):
                sub.apply_plan_snapshot(default_plan)
                migrated += 1
        if migrated:
            await self.session.flush()
        return migrated
