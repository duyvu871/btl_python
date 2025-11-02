"""
Use case: Login a user.
"""
from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.env import env
from src.core.database.models.user import User
from src.core.security.password import verify_password
from src.core.security.token import create_access_token
from src.modules.auth.schema import UserRead, LoginResponse
from src.modules.user.repository import UserRepository, get_user_repository

@dataclass
class LoginUseCaseExecuteResult:
    access_token: str
    user: User

class LoginUseCase:
    """
    Use case for logging in a user.
    """
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo


    async def execute(self, db: AsyncSession, email: str, password: str) -> LoginUseCaseExecuteResult:
        """
        Execute the use case.
        """
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(password, str(user.password)):
            raise ValueError("Incorrect email or password")

        if not user.verified:
            raise ValueError("Email not verified. Please verify your email before logging in.")

        access_token_expires = timedelta(minutes=env.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        return LoginUseCaseExecuteResult(access_token, user)


def get_login_use_case(user_repo: UserRepository = Depends(get_user_repository)) -> LoginUseCase:
    """
    Dependency injector for LoginUseCase.
    """
    return LoginUseCase(user_repo)