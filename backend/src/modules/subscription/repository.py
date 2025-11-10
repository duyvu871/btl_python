"""
Repository layer for subscription module.
Handles database queries for Plan and UserSubscription models.
"""
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models.plan import Plan, PlanType, BillingCycle
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
        """
        Get a plan by its unique code.

        Args:
            code: Plan code (e.g., 'FREE', 'BASIC', 'PREMIUM')

        Returns:
            Plan instance or None if not found
        """
        query = select(Plan).where(Plan.code == code)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_active_plans(self) -> list[Plan]:
        """
        List all active plans.

        Returns:
            List of Plan instances
        """
        query = select(Plan).order_by(Plan.plan_cost)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_default_plan(self) -> Plan | None:
        """
        Get the default FREE plan.

        Returns:
            FREE Plan instance or None
        """
        return await self.get_by_code("FREE")

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

        now = datetime.now(timezone.utc)

        if billing_cycle == BillingCycle.MONTHLY:
            cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if cycle_start.month == 12:
                cycle_end = cycle_start.replace(year=cycle_start.year + 1, month=1)
            else:
                cycle_end = cycle_start.replace(month=cycle_start.month + 1)
        elif billing_cycle == BillingCycle.YEARLY:
            cycle_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            cycle_end = cycle_start.replace(year=cycle_start.year + 1)
        elif billing_cycle == BillingCycle.LIFETIME:
            # For lifetime, set cycle_end to a far future date
            cycle_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            cycle_end = cycle_start.replace(year=cycle_start.year + 100)  # Arbitrary far future
        else:
            # Fallback to monthly
            cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if cycle_start.month == 12:
                cycle_end = cycle_start.replace(year=cycle_start.year + 1, month=1)
            else:
                cycle_end = cycle_start.replace(month=cycle_start.month + 1)

        return cycle_start, cycle_end

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
        """
        Check if user has available quota for creating a new recording.

        Args:
            user_id: User UUID

        Returns:
            Tuple of (has_quota: bool, error_message: str)
            If has_quota is True, error_message is empty.
        """
        subscription = await self.get_active_subscription(user_id)

        if not subscription:
            return False, "No active subscription found"

        # Check usage count limit
        if subscription.usage_count >= subscription.plan.monthly_usage_limit:
            return False, f"Monthly usage limit reached ({subscription.plan.monthly_usage_limit} recordings)"

        # Check minutes limit (convert to seconds)
        max_seconds = subscription.plan.monthly_minutes * 60
        if subscription.used_seconds >= max_seconds:
            return False, f"Monthly time limit reached ({subscription.plan.monthly_minutes} minutes)"

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
        """
        Get usage statistics for a user's subscription.

        Args:
            user_id: User UUID

        Returns:
            Dictionary containing usage statistics:
            {
                'usage_count': int,
                'monthly_usage_limit': int,
                'remaining_count': int,
                'used_seconds': int,
                'monthly_seconds': int,
                'remaining_seconds': int,
                'used_minutes': float,
                'monthly_minutes': int,
                'remaining_minutes': float
            }
        """
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

        monthly_seconds = subscription.plan.monthly_minutes * 60
        remaining_seconds = max(0, monthly_seconds - subscription.used_seconds)
        remaining_count = max(0, subscription.plan.monthly_usage_limit - subscription.usage_count)

        return {
            'usage_count': subscription.usage_count,
            'monthly_usage_limit': subscription.plan.monthly_usage_limit,
            'remaining_count': remaining_count,
            'used_seconds': subscription.used_seconds,
            'monthly_seconds': monthly_seconds,
            'remaining_seconds': remaining_seconds,
            'used_minutes': round(subscription.used_seconds / 60, 2),
            'monthly_minutes': subscription.plan.monthly_minutes,
            'remaining_minutes': round(remaining_seconds / 60, 2)
        }

    async def reset_cycle(self, user_id: UUID) -> None:
        """
        Reset the subscription cycle for a user.
        This is typically called by a scheduled task at the end of each billing cycle.

        Args:
            user_id: User UUID
        """
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return

        billing_cycle = subscription.plan.billing_cycle

        if billing_cycle == BillingCycle.LIFETIME:
            # Lifetime plans don't need reset
            return

        # 1. Reset usage_count to 0
        subscription.usage_count = 0
        
        # 2. Reset used_seconds to 0
        subscription.used_seconds = 0
        
        # 3. Update cycle_start and cycle_end based on billing_cycle
        cycle_start, cycle_end = self.calculate_cycle_dates(billing_cycle)

        subscription.cycle_start = cycle_start
        subscription.cycle_end = cycle_end
        
        await self.session.flush()
