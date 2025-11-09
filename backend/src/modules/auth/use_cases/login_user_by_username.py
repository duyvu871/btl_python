"""
Use case: Login a user by username.
"""

from datetime import timedelta

from fastapi import Depends
from sqlmodel import select

from src.core.config.env import env
from src.core.database.models.user import User
from src.core.security.password import verify_password
from src.core.security.token import create_access_token
from src.shared.uow import UnitOfWork, get_uow


class LoginByUsernameUseCase:
    """
    Use case for logging in a user by username.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, username: str, password: str) -> dict:
        """
        Execute the use case.
        """
        result = await self.uow.session.execute(select(User).where(User.user_name == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, str(user.password)):
            raise ValueError("Invalid credentials")

        access_token_expires = timedelta(minutes=env.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}


def get_login_by_username_use_case(uow: UnitOfWork = Depends(get_uow)) -> LoginByUsernameUseCase:
    """
    Dependency injector for LoginByUsernameUseCase.
    """
    return LoginByUsernameUseCase(uow)
