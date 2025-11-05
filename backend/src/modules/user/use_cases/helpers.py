"""
Helper class for user use cases.
Provides convenient wrappers around use cases with dependency injection support.
"""

from uuid import UUID

from fastapi import Depends

from src.core.database.models.user import User
from src.modules.user.schema import UserAdminCreate, UserUpdate
from src.modules.user.use_cases.list_users import ListUsersUseCase
from src.modules.user.use_cases.get_user_by_id_use_case import GetUserByIdUseCase
from src.modules.user.use_cases.create_user import CreateUserUseCase
from src.modules.user.use_cases.update_user import UpdateUserUseCase
from src.modules.user.use_cases.delete_user import DeleteUserUseCase
from src.modules.user.use_cases.get_user_stats import GetUserStatsUseCase
from src.modules.user.use_cases.bulk_action_users import BulkActionUsersUseCase
from src.shared.uow import UnitOfWork, get_uow


class UserUseCase:
    """
    Helper class that wraps user use cases.
    Designed to be used with FastAPI dependency injection.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize helper with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow
        self._list_users_use_case = ListUsersUseCase(uow)
        self._get_user_by_id_use_case = GetUserByIdUseCase(uow)
        self._create_user_use_case = CreateUserUseCase(uow)
        self._update_user_use_case = UpdateUserUseCase(uow)
        self._delete_user_use_case = DeleteUserUseCase(uow)
        self._get_user_stats_use_case = GetUserStatsUseCase(uow)
        self._bulk_action_users_use_case = BulkActionUsersUseCase(uow)

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
        return await self._list_users_use_case.execute(page, page_size, search, role, verified)

    async def get_user_by_id(self, uid: str):
        """
        Get user by ID.
        """
        return await self._get_user_by_id_use_case.execute(uid)

    async def create_user(self, user_data: UserAdminCreate) -> User:
        """
        Create a new user.
        """
        return await self._create_user_use_case.execute(user_data)

    async def update_user(self, user_id: UUID, user_update: UserUpdate, current_admin: User) -> User:
        """
        Update a user.
        """
        return await self._update_user_use_case.execute(user_id, user_update, current_admin)

    async def delete_user(self, user_id: UUID, current_admin: User) -> None:
        """
        Delete a user.
        """
        return await self._delete_user_use_case.execute(user_id, current_admin)

    async def get_user_stats(self) -> dict:
        """
        Get user statistics.
        """
        return await self._get_user_stats_use_case.execute()

    async def bulk_action_users(self, user_ids: list[UUID], action: str, current_admin: User) -> dict:
        """
        Perform bulk actions on users.
        """
        return await self._bulk_action_users_use_case.execute(user_ids, action, current_admin)


def get_user_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> UserUseCase:
    """
    FastAPI dependency to get UserUseCase instance.

    Returns:
        UserUseCase instance
    """
    return UserUseCase(uow)

