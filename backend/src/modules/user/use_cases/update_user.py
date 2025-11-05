"""
Use case: Update a user.
"""

from uuid import UUID

from src.core.database.models.user import Role, User
from src.modules.user.schema import UserUpdate
from src.shared.uow import UnitOfWork


class UpdateUserUseCase:
    """
    Use case for updating a user.

    Responsibilities:
    - Fetch user by ID
    - Validate permissions
    - Update user fields
    - Return updated user
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize use case with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow

    async def execute(self, user_id: UUID, user_update: UserUpdate, current_admin: User) -> User:
        """
        Execute the use case.

        Args:
            user_id: User ID
            user_update: Update data
            current_admin: Current admin user

        Returns:
            Updated user

        Raises:
            ValueError: If user not found or permission denied
        """
        user = await self.uow.user_repo.get(str(user_id))

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
            update_data[field] = value

        updated_user = await self.uow.user_repo.update(str(user_id), update_data)

        return updated_user
