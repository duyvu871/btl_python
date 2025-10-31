from src.core.database.models.user import User
from src.core.security.password import PasswordManager
from src.modules.auth.schemas import UserCreate
from src.modules.user.repository import UserRepository


class RegisterUserUseCase:
    """
    Use case for registering a new user in the auth module.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.password_manager = PasswordManager()

    async def execute(self, user_data: UserCreate) -> User:
        """
        Execute the use case to register a user.
        :param user_data: UserCreate schema instance
        :return: Created User instance
        :raises ValueError: If user with email already exists
        """
        # Check if user already exists
        existing = await self.user_repo.get_by_email(str(user_data.email))
        if existing:
            raise ValueError("User with this email already exists")

        # Hash the password
        hashed = self.password_manager.hash_password(user_data.password)

        # Prepare data for creation
        data = user_data.model_dump()
        data['password'] = hashed

        try:
            # Create the user
            user = await self.user_repo.create(data)
            return user
        except Exception as e:
            raise ValueError(f"Failed to register user: {str(e)}") from e
