"""Helper class for chat use cases with dependency injection support."""

from typing import Any
from uuid import UUID

from fastapi import Depends

from src.core.database.models.chat_session import ChatSession
from src.modules.chat.schema import (
    ChatMessageRead,
    ChatSessionRead,
    CreateMessageRequest,
    CreateSessionRequest,
    UpdateSessionRequest,
)
from src.modules.chat.use_cases.add_message_use_case import AddMessageUseCase
from src.modules.chat.use_cases.create_session_use_case import CreateSessionUseCase
from src.modules.chat.use_cases.delete_session_use_case import DeleteSessionUseCase
from src.modules.chat.use_cases.get_session_use_case import GetSessionUseCase
from src.modules.chat.use_cases.list_sessions_use_case import ListSessionsUseCase
from src.modules.chat.use_cases.update_session_use_case import UpdateSessionUseCase
from src.shared.uow import UnitOfWork, get_uow


def _session_to_read(session: ChatSession) -> ChatSessionRead:
    """Convert SQLAlchemy ChatSession to Pydantic ChatSessionRead, avoiding lazy loading."""
    return ChatSessionRead(
        id=session.id,
        user_id=session.user_id,
        recording_id=session.recording_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=None,  # Don't include messages to avoid lazy loading
    )


class ChatUseCase:
    """
    Helper class that wraps chat use cases.
    Designed to be used with FastAPI dependency injection.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize helper with unit of work."""
        self.uow = uow
        self._create_session = CreateSessionUseCase(uow)
        self._get_session = GetSessionUseCase(uow)
        self._list_sessions = ListSessionsUseCase(uow)
        self._update_session = UpdateSessionUseCase(uow)
        self._delete_session = DeleteSessionUseCase(uow)
        self._add_message = AddMessageUseCase(uow)

    async def create_session(
        self,
        user_id: UUID,
        request: CreateSessionRequest
    ) -> ChatSessionRead:
        """Create a new chat session."""
        session = await self._create_session.execute(user_id, request)
        return _session_to_read(session)

    async def get_session(self, user_id: UUID, session_id: UUID) -> ChatSessionRead:
        """Get session details."""
        session = await self._get_session.execute(user_id, session_id)
        return _session_to_read(session)

    async def list_sessions(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        recording_id: UUID | None = None
    ) -> dict[str, Any]:
        """List user's chat sessions."""
        sessions, total = await self._list_sessions.execute(user_id, page, per_page, recording_id)
        return {
            "data": [_session_to_read(s) for s in sessions],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    async def update_session(
        self,
        user_id: UUID,
        session_id: UUID,
        request: UpdateSessionRequest
    ) -> ChatSessionRead:
        """Update session title."""
        session = await self._update_session.execute(user_id, session_id, request)
        return _session_to_read(session)

    async def delete_session(self, user_id: UUID, session_id: UUID) -> bool:
        """Delete a session."""
        return await self._delete_session.execute(user_id, session_id)

    async def add_user_message(
        self,
        user_id: UUID,
        session_id: UUID,
        request: CreateMessageRequest
    ) -> ChatMessageRead:
        """Add user message to session."""
        message = await self._add_message.add_user_message(user_id, session_id, request)
        return ChatMessageRead.model_validate(message)

    async def add_assistant_message(
        self,
        user_id: UUID,
        session_id: UUID,
        content: str,
        sources: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> ChatMessageRead:
        """Add assistant message to session."""
        message = await self._add_message.add_assistant_message(
            user_id,
            session_id,
            content,
            sources,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )
        return ChatMessageRead.model_validate(message)

    async def get_session_messages(self, user_id: UUID, session_id: UUID) -> list[ChatMessageRead]:
        """Get all messages in session."""
        # Verify ownership first
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")

        # Then fetch messages
        messages = await self.uow.chat_message_repo.get_session_messages(session_id)
        return [ChatMessageRead.model_validate(m) for m in messages]


async def get_chat_usecase(uow: UnitOfWork = Depends(get_uow)) -> ChatUseCase:
    """Dependency injection for ChatUseCase."""
    return ChatUseCase(uow)

