"""Use case for updating chat session."""

from uuid import UUID

from src.core.database.models.chat_session import ChatSession
from src.modules.chat.schema import UpdateSessionRequest
from src.shared.uow import UnitOfWork


class UpdateSessionUseCase:
    """Update chat session title."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        session_id: UUID,
        request: UpdateSessionRequest
    ) -> ChatSession:
        """
        Update session title with authorization.

        Args:
            user_id: User UUID
            session_id: ChatSession UUID
            request: UpdateSessionRequest with new title

        Returns:
            Updated ChatSession

        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        # Verify ownership
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")

        # Update title
        success = await self.uow.chat_session_repo.update_title(session_id, request.title)
        if not success:
            raise ValueError("Failed to update session title")

        # Fetch updated session
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        return session

