"""Use case for adding messages to chat session."""

from uuid import UUID

from src.core.database.models.chat_message import ChatMessage, MessageRole
from src.modules.chat.schema import CreateMessageRequest
from src.shared.uow import UnitOfWork


class AddMessageUseCase:
    """Add user or assistant message to chat session."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def add_user_message(
        self,
        user_id: UUID,
        session_id: UUID,
        request: CreateMessageRequest
    ) -> ChatMessage:
        """
        Add user message to session.

        Args:
            user_id: User UUID
            session_id: ChatSession UUID
            request: CreateMessageRequest with content

        Returns:
            Created ChatMessage

        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        # Verify session ownership
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")

        message = await self.uow.chat_message_repo.create_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=request.content,
        )
        return message

    async def add_assistant_message(
        self,
        user_id: UUID,
        session_id: UUID,
        content: str,
        sources: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> ChatMessage:
        """
        Add assistant message to session.

        Args:
            user_id: User UUID
            session_id: ChatSession UUID
            content: Message content
            sources: RAG sources (optional)
            prompt_tokens: Prompt token count (optional)
            completion_tokens: Completion token count (optional)
            total_tokens: Total token count (optional)

        Returns:
            Created ChatMessage

        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        # Verify session ownership
        session = await self.uow.chat_session_repo.get_by_id_and_user(session_id, user_id)
        if not session:
            raise ValueError("Session not found or access denied")

        message = await self.uow.chat_message_repo.create_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            sources=sources,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        return message

