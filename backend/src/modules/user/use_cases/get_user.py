"""
Use case: Get a specific user.
"""

from uuid import UUID

from src.core.database.models.user import User
from src.shared.uow import UnitOfWork


class GetUserUseCase:
    """
    Use case for getting a specific user.

    Responsibilities:
    - Fetch user by ID
    - Return user if found
    """

    async def execute(self, uow: UnitOfWork, user_id: UUID) -> User:
        """
        Execute the use case.

        Args:
            uow: Unit of work
            user_id: User ID

        Returns:
            User object

        Raises:
            ValueError: If user not found
        """
        user = await uow.user_repo.get(str(user_id))

        if not user:
            raise ValueError("User not found")

        return user
