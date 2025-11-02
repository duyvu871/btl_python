"""
Helper class for admin use cases.
Provides convenient wrappers around use cases.
"""

from .bulk_action_users import BulkActionUsersUseCase
from .create_user import CreateUserUseCase
from .delete_user import DeleteUserUseCase
from .get_user import GetUserUseCase
from .get_user_stats import GetUserStatsUseCase
from .list_users import ListUsersUseCase
from .update_user import UpdateUserUseCase


class AdminUseCase:
    """
    Helper class that wraps admin use cases.
    Designed to be used with FastAPI dependency injection.

    Example:
        @app.get("/admin/users")
        async def list_users(
            helper: AdminUseCase = Depends(get_admin_usecase)
        ):
            result = await helper.list_users(db, page, page_size, search, role, verified)
    """

    def __init__(self):
        pass

    async def list_users(self, db, page=1, page_size=10, search=None, role=None, verified=None):
        """
        List users with pagination and filters.

        Args:
            db: Database session
            page: Page number
            page_size: Items per page
            search: Search term
            role: Role filter
            verified: Verification filter

        Returns:
            Dict with total, page, page_size, users

        Raises:
            ValueError: If invalid role
        """
        use_case = ListUsersUseCase()
        return await use_case.execute(db, page, page_size, search, role, verified)

    async def get_user(self, db, user_id):
        """
        Get a specific user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object

        Raises:
            ValueError: If user not found
        """
        use_case = GetUserUseCase()
        return await use_case.execute(db, user_id)

    async def update_user(self, db, user_id, user_update, current_admin):
        """
        Update a user.

        Args:
            db: Database session
            user_id: User ID
            user_update: Update data
            current_admin: Current admin user

        Returns:
            Updated user

        Raises:
            ValueError: If user not found or permission denied
        """
        use_case = UpdateUserUseCase()
        return await use_case.execute(db, user_id, user_update, current_admin)

    async def delete_user(self, db, user_id, current_admin):
        """
        Delete a user.

        Args:
            db: Database session
            user_id: User ID
            current_admin: Current admin user

        Raises:
            ValueError: If user not found or permission denied
        """
        use_case = DeleteUserUseCase()
        return await use_case.execute(db, user_id, current_admin)

    async def get_user_stats(self, db):
        """
        Get user statistics.

        Args:
            db: Database session

        Returns:
            Dict with statistics
        """
        use_case = GetUserStatsUseCase()
        return await use_case.execute(db)

    async def bulk_action_users(self, db, user_ids, action, current_admin):
        """
        Perform bulk action on users.

        Args:
            db: Database session
            user_ids: List of user IDs
            action: Action to perform
            current_admin: Current admin user

        Returns:
            Dict with results

        Raises:
            ValueError: If invalid action or permission denied
        """
        use_case = BulkActionUsersUseCase()
        return await use_case.execute(db, user_ids, action, current_admin)

    async def create_user(self, db, user_data):
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
        """
        use_case = CreateUserUseCase()
        return await use_case.execute(db, user_data)


def get_admin_usecase() -> AdminUseCase:
    """
    Dependency injection for AdminUseCase.
    """
    return AdminUseCase()
