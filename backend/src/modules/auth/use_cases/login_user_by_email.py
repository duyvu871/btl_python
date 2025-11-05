"""
Use case: Login a user.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends

from src.core.config.env import env, global_logger_name
from src.core.database.models.user import User
from src.core.security.password import verify_password
from src.core.security.token import create_access_token
from src.shared.uow import UnitOfWork, get_uow

logger = logging.getLogger(global_logger_name)

@dataclass
class LoginUseCaseExecuteResult:
    access_token: str
    user: User


class LoginUseCase:
    """
    Use case for logging in a user.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.user_repo = uow.user_repo

    async def execute(self, email: str, password: str) -> LoginUseCaseExecuteResult:
        """
        Execute the use case.

        """
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(str(user.password), password):
            # print("Invalid credentials")
            raise ValueError("Incorrect email or password")

        if not user.verified:
            # print("Email not verified")
            raise ValueError("Email not verified. Please verify your email before logging in.")

        try:
            access_token_expires = timedelta(minutes=env.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
            return LoginUseCaseExecuteResult(access_token, user)
        except Exception as e:
            logger.error(f"Error login user: {e}")
            raise ValueError(f"Failed to login user") from e


def get_login_use_case(uow: UnitOfWork = Depends(get_uow)) -> LoginUseCase:
    """
    Dependency injector for LoginUseCase.
    """
    return LoginUseCase(uow)
