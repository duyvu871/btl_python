"""
Use case: Create a new user.
"""

from src.core.database.models.user import Role, User
from src.core.security.password import hash_password
from src.modules.user.schema import UserAdminCreate
from src.shared.uow import UnitOfWork


class CreateUserUseCase:
    """
    Use case for creating a new user.

    Responsibilities:
    - Validate user doesn't exist
    - Hash password
    - Create and save user
    - Return created user
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize use case with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow

    async def execute(self, user_data: UserAdminCreate) -> User:
        """
        Execute the use case.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        existing_user = await self.uow.user_repo.get_by_email(str(user_data.email))

        if existing_user:
            raise ValueError("User with this email already exists")

        # Generate user_name if not provided
        user_name = user_data.user_name or str(user_data.email).split("@")[0]

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user data dict
        user_dict = {
            "user_name": user_name,
            "email": str(user_data.email),
            "password": hashed_password,
            "role": Role[user_data.role.upper()],
            "verified": user_data.verified,
        }

        new_user = await self.uow.user_repo.create(user_dict)

        return new_user
