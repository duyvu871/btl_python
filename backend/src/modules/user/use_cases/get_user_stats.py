"""
Use case: Get user statistics.
"""

from src.shared.uow import UnitOfWork


class GetUserStatsUseCase:
    """
    Use case for getting user statistics.

    Responsibilities:
    - Calculate various user counts
    - Return statistics
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize use case with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow

    async def execute(self) -> dict:
        """
        Execute the use case.

        Returns:
            Dict with statistics
        """
        return await self.uow.user_repo.get_user_stats()
