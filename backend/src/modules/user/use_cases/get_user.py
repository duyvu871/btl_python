"""
Use case: Get a specific user.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models import User


class GetUserUseCase:
    """
    Use case for getting a specific user.

    Responsibilities:
    - Fetch user by ID
    - Return user if found
    """

    async def execute(self, db: AsyncSession, user_id: UUID) -> User:
        """
        Execute the use case.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object

        Raises:
            ValueError: If user not found
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        return user
