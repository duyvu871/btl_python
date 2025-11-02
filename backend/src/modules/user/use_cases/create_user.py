"""
Use case: Create a new user.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models.user import Role, User
from src.core.security.password import hash_password
from src.modules.user.schema import UserAdminCreate


class CreateUserUseCase:
    """
    Use case for creating a new user.

    Responsibilities:
    - Validate user doesn't exist
    - Hash password
    - Create and save user
    - Return created user
    """

    async def execute(self, db: AsyncSession, user_data: UserAdminCreate) -> User:
        """
        Execute the use case.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
        """
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User with this email already exists")

        # Generate user_name if not provided
        user_name = user_data.user_name or str(user_data.email).split("@")[0]

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        new_user = User(
            user_name=user_name,
            email=str(user_data.email),
            password=hashed_password,
            role=Role[user_data.role.upper()],
            verified=user_data.verified,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
