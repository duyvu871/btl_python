"""
Helper class for auth use cases.
Provides convenient wrappers around use cases with dependency injection support.
"""

from fastapi import Depends

from src.modules.auth.schema import UserCreate
from src.modules.auth.use_cases.login_user_by_email import LoginUseCase
from src.modules.auth.use_cases.register_user_use_case import RegisterUserUseCase
from src.modules.verification.use_cases import VerificationUseCase, get_verification_usecase
from src.shared.uow import UnitOfWork, get_uow


class AuthUseCase:
    """
    Helper class that wraps auth use cases.
    Designed to be used with FastAPI dependency injection.
    """

    def __init__(self, uow: UnitOfWork, verification_use_case: VerificationUseCase):
        """
        Initialize helper with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow
        self.verification_use_case = verification_use_case
        self._login_use_case = LoginUseCase(uow)
        self._register_use_case = RegisterUserUseCase(uow, verification_use_case)

    async def login(self, email: str, password: str):
        """
        Login user by email.
        """
        return await self._login_use_case.execute(email, password)

    async def register(self, user_data: UserCreate):
        """
        Register a new user.
        """
        return await self._register_use_case.execute(user_data)


async def get_auth_usecase(
    uow: UnitOfWork = Depends(get_uow),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase),
) -> AuthUseCase:
    """
    FastAPI dependency to get AuthUseCase instance.

    Returns:
        AuthUseCase instance
    """
    return AuthUseCase(uow, verification_use_case)
