from typing import Any, Coroutine, Sequence
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.core.database.db import get_db
from src.core.database.models.user import Role, User
from src.shared.base.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    Repository for User model.
    Inherits CRUD operations from BaseRepository.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """
        Get a user by email.
        :param email: User's email
        :return: User instance or None
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        role: str | None = None,
        verified: bool | None = None,
    ) -> dict:
        """
        List users with pagination and filters.
        """
        # Build query
        query = select(User)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.where(or_(User.email.ilike(search_term), User.user_name.ilike(search_term)))

        if role:
            try:
                role_enum = Role[role.upper()]
                query = query.where(User.role == role_enum)
            except KeyError:
                raise ValueError(f"Invalid role: {role}. Must be 'user' or 'admin'")

        if verified is not None:
            query = query.where(User.verified == verified)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

        # Execute query
        result = await self.session.execute(query)
        users = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "users": users,
        }

    async def get_by_ids(self, user_ids: list[str | UUID]) -> Sequence[User]:
        """
        Get users by a list of IDs.
        :param user_ids: List of user IDs
        :return: List of User instances
        """
        query = select(User).where(User.id.in_(user_ids))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def bulk_update_verified_status(
            self, user_ids: list[str | UUID], status: bool
    ):
        """
        update 'verified' status for multiple users.
        :param user_ids: 
        :param status: 
        :return: 
        """""
        query = (
            update(User)
            .where(User.id.in_(user_ids))
            .values(verified=status)
        )
        await self.session.execute(query)

    async def bulk_update_role(
            self, user_ids: list[str | UUID], role: Role
    ):
        """
        update 'role' for multiple users.
        :param user_ids:
        :param role:
        :return:
        """
        query = (
            update(User)
            .where(User.id.in_(user_ids))
            .values(role=role)
        )
        await self.session.execute(query)

    async def bulk_delete(self, user_ids: list[str | UUID]):
        """
        Delete multiple users by IDs.
        :param user_ids:
        :return:
        """
        query = delete(User).where(User.id.in_(user_ids))
        await self.session.execute(query)

    async def get_user_stats(self) -> dict:
        """
        Get user statistics.
        """
        seven_days_ago = datetime.now() - timedelta(days=7)

        query = select(
            func.count(User.id).label("total_users"),
            func.count(User.id).filter(User.verified == True).label("verified_users"),
            func.count(User.id).filter(User.role == Role.ADMIN).label("admin_users"),
            func.count(User.id).filter(User.created_at >= seven_days_ago).label("recent_users")
        )

        result = await self.session.execute(query)
        stats = result.one()

        return {
            "total_users": stats.total_users,
            "verified_users": stats.verified_users,
            "unverified_users": stats.total_users - stats.verified_users,
            "admin_users": stats.admin_users,
            "regular_users": stats.total_users - stats.admin_users,
            "recent_users": stats.recent_users,
        }


# FastAPI Dependency
def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    FastAPI dependency to get UserRepository instance.

    Returns:
        UserRepository instance
    """
    return UserRepository(db)
