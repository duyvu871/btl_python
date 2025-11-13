"""Use case for listing chat sessions."""

from uuid import UUID

from src.core.database.models.chat_session import ChatSession
from src.shared.uow import UnitOfWork


class ListSessionsUseCase:
    """List all chat sessions for a user."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        recording_id: UUID | None = None
    ) -> tuple[list[ChatSession], int]:
        """
        List user's chat sessions with pagination.

        Args:
            user_id: User UUID
            page: Page number (1-based)
            per_page: Items per page
            recording_id: Optional filter by recording ID

        Returns:
            Tuple of (sessions list, total count)
        """
        filters = {}
        if recording_id:
            filters["recording_id"] = recording_id

        sessions, total = await self.uow.chat_session_repo.list_user_sessions(
            user_id, page, per_page, filters
        )
        return sessions, total

