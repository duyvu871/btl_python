"""
Use case: Get user statistics.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models.user import Role, User


class GetUserStatsUseCase:
    """
    Use case for getting user statistics.

    Responsibilities:
    - Calculate various user counts
    - Return statistics
    """

    async def execute(self, db: AsyncSession) -> dict:
        """
        Execute the use case.

        Args:
            db: Database session

        Returns:
            Dict with statistics
        """
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar_one()

        # Verified users
        verified_users_result = await db.execute(select(func.count(User.id)).where(User.verified))
        verified_users = verified_users_result.scalar_one()

        # Admin users
        admin_users_result = await db.execute(select(func.count(User.id)).where(User.role == Role.ADMIN))
        admin_users = admin_users_result.scalar_one()

        # Recent users (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_users_result = await db.execute(select(func.count(User.id)).where(User.created_at >= seven_days_ago))
        recent_users = recent_users_result.scalar_one()

        return {
            "total_users": total_users,
            "verified_users": verified_users,
            "unverified_users": total_users - verified_users,
            "admin_users": admin_users,
            "regular_users": total_users - admin_users,
            "recent_users": recent_users,
        }
