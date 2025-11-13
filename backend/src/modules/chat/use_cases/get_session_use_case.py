"""Use case for getting chat session details."""

from uuid import UUID

from src.core.database.models.chat_session import ChatSession
from src.shared.uow import UnitOfWork


class GetSessionUseCase:
    """Get chat session details with authorization."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID, session_id: UUID) -> ChatSession:
        """
        Get session details (without messages).

        Args:
            user_id: User UUID
            session_id: ChatSession UUID

        Returns:
            ChatSession instance

        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")
        return session

