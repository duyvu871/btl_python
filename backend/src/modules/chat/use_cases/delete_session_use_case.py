"""Use case for deleting chat session."""

from uuid import UUID

from src.shared.uow import UnitOfWork


class DeleteSessionUseCase:
    """Delete a chat session."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID, session_id: UUID) -> bool:
        """
        Delete session with authorization.

        Args:
            user_id: User UUID
            session_id: ChatSession UUID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        # Verify ownership
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")

        # Delete session
        return await self.uow.chat_session_repo.delete_by_id(session_id)

