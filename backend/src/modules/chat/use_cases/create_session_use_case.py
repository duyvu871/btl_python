"""Use case for creating a chat session."""

from uuid import UUID

from src.core.database.models.chat_session import ChatSession
from src.modules.chat.schema import CreateSessionRequest
from src.shared.uow import UnitOfWork


class CreateSessionUseCase:
    """Create a new chat session for a recording."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID, request: CreateSessionRequest) -> ChatSession:
        """
        Create a new chat session.

        Args:
            user_id: User UUID
            request: CreateSessionRequest with recording_id and title

        Returns:
            Created ChatSession instance

        Raises:
            ValueError: If recording not found or doesn't belong to user
        """
        # Verify recording exists and belongs to user
        recording = await self.uow.recording_repo.get(request.recording_id)
        if not recording or recording.user_id != user_id:
            raise ValueError("Recording not found or access denied")

        # Create session
        session = await self.uow.chat_session_repo.create({
            "user_id": user_id,
            "recording_id": request.recording_id,
            "title": request.title,
        })

        return session

