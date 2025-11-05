"""
Use case: Delete a user.
"""

from uuid import UUID

from src.core.database.models.user import User
from src.shared.uow import UnitOfWork


class DeleteUserUseCase:
    """
    Use case for deleting a user.

    Responsibilities:
    - Fetch user by ID
    - Validate permissions
    - Delete user
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize use case with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow

    async def execute(self, user_id: UUID, current_admin: User) -> None:
        """
        Execute the use case.

        Args:
            user_id: User ID
            current_admin: Current admin user

        Raises:
            ValueError: If user not found or permission denied
        """
        user = await self.uow.user_repo.get(str(user_id))

        if not user:
            raise ValueError("User not found")

        # Prevent admin from deleting themselves
        if user.id == current_admin.id:
            raise ValueError("Cannot delete your own account")

        await self.uow.user_repo.delete(str(user_id))
