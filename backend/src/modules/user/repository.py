from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models.user import User
from src.shared.base.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    Repository for User model.
    Inherits CRUD operations from BaseRepository.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User:
        """
        Get a user by email.
        :param email: User's email
        :return: User instance or None
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()