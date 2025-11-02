"""
Use case: Delete a user.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models import User


class DeleteUserUseCase:
    """
    Use case for deleting a user.

    Responsibilities:
    - Fetch user by ID
    - Validate permissions
    - Delete user
    """

    async def execute(self, db: AsyncSession, user_id: UUID, current_admin: User) -> None:
        """
        Execute the use case.

        Args:
            db: Database session
            user_id: User ID
            current_admin: Current admin user

        Raises:
            ValueError: If user not found or permission denied
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Prevent admin from deleting themselves
        if user.id == current_admin.id:
            raise ValueError("Cannot delete your own account")

        await db.delete(user)
        await db.commit()
