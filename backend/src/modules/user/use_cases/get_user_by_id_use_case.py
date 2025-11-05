from src.shared.uow import UnitOfWork


class GetUserByIdUseCase:
    """
    Use case for getting a user by ID.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize use case with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow

    async def execute(self, uid: str):
        """
        Execute the use case to get user by ID.
        :param uid: User ID
        :return: User instance or None
        """
        return await self.uow.user_repo.get(uid)
