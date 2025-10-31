from src.modules.user.repository import UserRepository


class RegisterUserUseCase:
    """
    Use case for registering a new user.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, data: dict):
        """
        Execute the use case to register a user.
        :param data: User data dictionary
        :return: Created User instance
        """
        return await self.user_repo.create(data)
