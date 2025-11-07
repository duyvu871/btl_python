# get current user from token
from datetime import datetime

import jwt
from dataclasses import dataclass
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.config.env import env
from src.core.database.db import get_db
from src.core.database.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api.md/v1/auth/token")

# get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, env.SECRET_KEY, algorithms=[env.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

@dataclass
class GetCurrentUserResult:
    user: User | None
    expires: datetime | None

async def get_current_user_without_throw(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> GetCurrentUserResult:
    try:
        payload = jwt.decode(token, env.SECRET_KEY, algorithms=[env.ALGORITHM])
        expires: datetime | None = payload.get("exp")
        email: str = payload.get("sub")
        if email is None:
            return GetCurrentUserResult(user=None, expires=None)
    except jwt.InvalidTokenError:
        return GetCurrentUserResult(user=None, expires=None)

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    return GetCurrentUserResult(user=user, expires=expires)

# require verified user
async def get_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return current_user


# require admin user
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for access."""
    from src.core.database.models.user import Role

    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
