"""
Use case: List users with pagination and filters.
"""

from src.shared.uow import UnitOfWork


class ListUsersUseCase:
    """
    Use case for listing users with pagination and filters.

    Responsibilities:
    - Build query with filters
    - Apply pagination
    - Return paginated results
    """

    async def execute(
        self,
        uow: UnitOfWork,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        role: str | None = None,
        verified: bool | None = None,
    ) -> dict:
        """
        Execute the use case.

        Args:
            uow: Unit of work
            page: Page number
            page_size: Items per page
            search: Search term for email or username
            role: Filter by role
            verified: Filter by verification status

        Returns:
            Dict with total, page, page_size, users list

        Raises:
            ValueError: If invalid role
        """
        return await uow.user_repo.list_users(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            verified=verified,
        )
