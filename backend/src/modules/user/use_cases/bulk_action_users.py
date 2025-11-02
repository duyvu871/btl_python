"""
Use case: Perform bulk actions on users.
"""

from uuid import UUID

from src.core.database.models.user import Role, User
from src.shared.uow import UnitOfWork


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
        self, uow: UnitOfWork, user_ids: list[UUID], action: str, current_admin: User
    ) -> dict:
        """
        Execute the use case.

        Args:
            uow: Unit of work
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

        # convert UUIDs to strings
        user_id_strs = [str(uid) for uid in user_ids]

        # check if current admin is in the list
        admin_id_str = str(current_admin.id)
        admin_in_list = admin_id_str in user_id_strs

        # prepare target IDs excluding admin if needed
        target_ids = [uid for uid in user_id_strs if uid != admin_id_str]

        updated_count = 0

        if action == "verify":
            await uow.user_repo.bulk_update_verified_status(user_id_strs, status=True)
            updated_count = len(user_id_strs)

        elif action == "unverify":
            if not target_ids:
                # this means only admin was in the list
                updated_count = 0
            else:
                await uow.user_repo.bulk_update_verified_status(target_ids, status=False)
                updated_count = len(target_ids)

        elif action == "promote":
            await uow.user_repo.bulk_update_role(user_id_strs, role=Role.ADMIN)
            updated_count = len(user_id_strs)

        elif action == "demote":
            if admin_in_list:
                raise ValueError("Cannot demote yourself")
            await uow.user_repo.bulk_update_role(user_id_strs, role=Role.USER)
            updated_count = len(user_id_strs)

        elif action == "delete":
            if admin_in_list:
                raise ValueError("Cannot delete your own account")
            await uow.user_repo.bulk_delete(user_id_strs)
            updated_count = len(user_id_strs)

        else:
            raise ValueError(f"Invalid action: {action}")

        return {
            "success": True,
            "action": action,
            "updated_count": updated_count,
            "total_requested": len(user_ids),
        }
