"""
Use case: Perform bulk actions on users.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.models.user import Role, User


class BulkActionUsersUseCase:
    """
    Use case for performing bulk actions on users.

    Responsibilities:
    - Fetch users by IDs
    - Validate permissions
    - Perform the specified action
    - Return results
    """

    async def execute(
        self, db: AsyncSession, user_ids: list[UUID], action: str, current_admin: User
    ) -> dict:
        """
        Execute the use case.

        Args:
            db: Database session
            user_ids: List of user IDs
            action: Action to perform (verify, unverify, promote, demote, delete)
            current_admin: Current admin user

        Returns:
            Dict with success, action, updated_count, total_requested

        Raises:
            ValueError: If invalid action or permission denied
        """
        if not user_ids:
            raise ValueError("No user IDs provided")

        # Fetch users
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = result.scalars().all()

        if not users:
            raise ValueError("No users found with provided IDs")

        # Check if admin is trying to modify themselves
        admin_in_list = any(user.id == current_admin.id for user in users)

        updated_count = 0

        if action == "verify":
            for user in users:
                if not user.verified:
                    user.verified = True
                    updated_count += 1

        elif action == "unverify":
            for user in users:
                if user.verified and user.id != current_admin.id:
                    user.verified = False
                    updated_count += 1

        elif action == "promote":
            for user in users:
                if user.role != Role.ADMIN:
                    user.role = Role.ADMIN
                    updated_count += 1

        elif action == "demote":
            if admin_in_list:
                raise ValueError("Cannot demote yourself")
            for user in users:
                if user.role == Role.ADMIN:
                    user.role = Role.USER
                    updated_count += 1

        elif action == "delete":
            if admin_in_list:
                raise ValueError("Cannot delete your own account")
            for user in users:
                await db.delete(user)
                updated_count += 1

        else:
            raise ValueError(f"Invalid action: {action}")

        await db.commit()

        return {
            "success": True,
            "action": action,
            "updated_count": updated_count,
            "total_requested": len(user_ids),
        }
