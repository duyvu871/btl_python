"""
Use case: Login a user.
"""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.config.env import env
from src.core.database.models.user import User
from src.core.security.password import verify_password
from src.core.security.token import create_access_token
from src.modules.auth.schemas import UserRead


class LoginUseCase:
    """
    Use case for logging in a user.
    """

    async def execute(self, db: AsyncSession, email: str, password: str) -> dict:
        """
        Execute the use case.
        """
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, str(user.password)):
            raise ValueError("Incorrect email or password")

        if not user.verified:
            raise ValueError("Email not verified. Please verify your email before logging in.")

        access_token_expires = timedelta(minutes=env.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        return {"access_token": access_token, "user": UserRead.model_validate(user)}
