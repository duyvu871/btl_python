"""
Use case: Update a user.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models.user import Role, User
from src.schemas.user import UserUpdate


class UpdateUserUseCase:
    """
    Use case for updating a user.

    Responsibilities:
    - Fetch user by ID
    - Validate permissions
    - Update user fields
    - Return updated user
    """

    async def execute(self, db: AsyncSession, user_id: UUID, user_update: UserUpdate, current_admin: User) -> User:
        """
        Execute the use case.

        Args:
            db: Database session
            user_id: User ID
            user_update: Update data
            current_admin: Current admin user

        Returns:
            Updated user

        Raises:
            ValueError: If user not found or permission denied
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Prevent admin from demoting themselves
        if user.id == current_admin.id and user_update.role and user_update.role.lower() != "admin":
            raise ValueError("Cannot change your own admin role")

        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "role":
                try:
                    value = Role[value.upper()]
                except KeyError:
                    raise ValueError(f"Invalid role: {value}. Must be 'user' or 'admin'")
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return user
