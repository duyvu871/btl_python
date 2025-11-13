"""
Repository layer for chat module.
Handles database queries for ChatSession and ChatMessage models.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models.chat_message import ChatMessage, MessageRole
from src.core.database.models.chat_session import ChatSession
from src.shared.base.base_repository import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    """
    Repository for ChatSession model.
    Manages CRUD operations and business queries for chat sessions.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(ChatSession, session)

    async def get_by_id_with_messages(self, session_id: UUID) -> ChatSession | None:
        """
        Get a chat session by ID with all its messages loaded.

        Args:
            session_id: ChatSession UUID

        Returns:
            ChatSession instance with messages loaded, or None if not found
        """
        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_user_sessions(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        filters: dict[str, Any] | None = None
    ) -> tuple[list[ChatSession], int]:
        """
        List chat sessions for a user with pagination and filters.

        Args:
            user_id: User UUID
            page: Page number (1-based)
            per_page: Items per page
            filters: Optional filters dict (recording_id, etc.)

        Returns:
            Tuple of (sessions list, total count)
        """
        query = select(ChatSession).where(ChatSession.user_id == user_id)

        # Apply filters
        if filters:
            if 'recording_id' in filters:
                query = query.where(ChatSession.recording_id == filters['recording_id'])

        # Get total count
        count_query = query.with_only_columns(func.count()).order_by(None)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * per_page
        query = query.order_by(ChatSession.updated_at.desc()).offset(offset).limit(per_page)

        result = await self.session.execute(query)
        sessions = list(result.scalars().all())

        return sessions, total

    async def get_by_id_and_user(self, session_id: UUID, user_id: UUID) -> ChatSession | None:
        """
        Get a chat session by ID and verify ownership.

        Args:
            session_id: ChatSession UUID
            user_id: User UUID

        Returns:
            ChatSession instance if found and belongs to user, None otherwise
        """
        query = (
            select(ChatSession)
            .where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_id_and_user_with_messages(self, session_id: UUID, user_id: UUID) -> ChatSession | None:
        """
        Get a chat session by ID with messages loaded.

        Args:
            session_id: ChatSession UUID
            user_id: User UUID

        Returns:
            ChatSession instance with messages loaded if found and belongs to user, None otherwise
        """
        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update_title(self, session_id: UUID, title: str) -> bool:
        """
        Update chat session title.

        Args:
            session_id: ChatSession UUID
            title: New title

        Returns:
            True if updated, False if not found
        """
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.session.execute(query)
        session = result.scalars().first()

        if not session:
            return False

        session.title = title
        await self.session.flush()
        return True

    async def delete_by_id(self, session_id: UUID) -> bool:
        """
        Delete a chat session by ID.

        Args:
            session_id: ChatSession UUID

        Returns:
            True if deleted, False if not found
        """
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.session.execute(query)
        session = result.scalars().first()

        if not session:
            return False

        await self.session.delete(session)
        await self.session.flush()
        return True


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """
    Repository for ChatMessage model.
    Manages CRUD operations for chat messages.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(ChatMessage, session)

    async def get_session_messages(self, session_id: UUID) -> list[ChatMessage]:
        """
        Get all messages in a chat session.

        Args:
            session_id: ChatSession UUID

        Returns:
            List of ChatMessage instances ordered by creation time
        """
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        sources: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> ChatMessage:
        """
        Create a new chat message.

        Args:
            session_id: ChatSession UUID
            role: Message role (user, assistant, system)
            content: Message content
            sources: RAG sources (optional)
            prompt_tokens: Prompt token count (optional)
            completion_tokens: Completion token count (optional)
            total_tokens: Total token count (optional)

        Returns:
            Created ChatMessage instance
        """
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        self.session.add(message)
        await self.session.flush()
        return message

