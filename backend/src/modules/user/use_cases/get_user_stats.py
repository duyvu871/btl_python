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

    async def execute(self, uow: UnitOfWork) -> dict:
        """
        Execute the use case.

        Args:
            uow: Unit of work

        Returns:
            Dict with statistics
        """
        return await uow.user_repo.get_user_stats()
