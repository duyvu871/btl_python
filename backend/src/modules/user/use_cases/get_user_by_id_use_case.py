from src.modules.user.repository import UserRepository


class GetUserByIdUseCase:
    """
    Use case for getting a user by ID.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, uid: str):
        """
        Execute the use case to get user by ID.
        :param uid: User ID
        :return: User instance or None
        """
        return await self.user_repo.get(uid)
