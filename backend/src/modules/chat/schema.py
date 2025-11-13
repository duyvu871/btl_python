"""
Chat module schemas for request/response validation.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.core.database.models.chat_message import MessageRole


class SourceItem(BaseModel):
    """Source segment from RAG."""

    text: str
    metadata: dict


class ChatMessageRead(BaseModel):
    """Chat message response schema."""

    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    sources: Optional[list[SourceItem]] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionRead(BaseModel):
    """Chat session response schema."""

    id: uuid.UUID
    user_id: uuid.UUID
    recording_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[list[ChatMessageRead]] = None

    class Config:
        from_attributes = True


class CreateSessionRequest(BaseModel):
    """Request to create a chat session."""

    recording_id: uuid.UUID
    title: str = Field(default="New Chat", max_length=255)


class UpdateSessionRequest(BaseModel):
    """Request to update a chat session."""

    title: str = Field(max_length=255)


class CreateMessageRequest(BaseModel):
    """Request to create a chat message."""

    content: str = Field(min_length=1)
    role: MessageRole = MessageRole.USER


class ChatCompletionRequest(BaseModel):
    """Request for AI chat completion."""

    query: str = Field(min_length=1)
    top_k: int = 10
    score_threshold: float = 0.1
    rerank_top_k: int = 3


class ChatCompletionResponse(BaseModel):
    """Response for chat completion with both user and assistant messages."""

    user_message: ChatMessageRead
    assistant_message: ChatMessageRead

    class Config:
        from_attributes = True
