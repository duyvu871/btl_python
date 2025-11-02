"""
Helper class for auth use cases.
Provides convenient wrappers around use cases with dependency injection support.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models.user import User
from src.modules.auth.use_cases.login_user_by_email import LoginUseCase
from src.modules.auth.use_cases.register_user_use_case import RegisterUserUseCase
from src.modules.user.repository import UserRepository, get_user_repository
from src.modules.verification.use_cases import VerificationUseCase


class AuthUseCase:
    """
    Helper class that wraps auth use cases.
    Designed to be used with FastAPI dependency injection.
    """

    def __init__(self, user_repo: UserRepository, verification_use_case: VerificationUseCase):
        """
        Initialize helper with user repository.

        Args:
            user_repo: UserRepository instance
        """
        self.user_repo = user_repo
        self.verification_use_case = verification_use_case
        self._login_use_case = LoginUseCase(user_repo)
        self._register_use_case = RegisterUserUseCase(user_repo, verification_use_case)

    async def login(self, db: AsyncSession, email: str, password: str) -> dict:
        """
        Login user by email.
        """
        return await self._login_use_case.execute(db, email, password)

    async def register(self, db: AsyncSession, user_data) -> User:
        """
        Register a new user.
        """
        return await self._register_use_case.execute(user_data)


async def get_auth_usecase(
    user_repo: UserRepository = Depends(get_user_repository),
    verification_use_case: VerificationUseCase = Depends(VerificationUseCase),
) -> AuthUseCase:
    """
    FastAPI dependency to get AuthUseCase instance.

    Returns:
        AuthUseCase instance
    """
    return AuthUseCase(user_repo, verification_use_case)
