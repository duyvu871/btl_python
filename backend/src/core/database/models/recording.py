from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.core.database.db import Base

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .segment import Segment
    from .transcript_chunk import TranscriptChunk
    from .user import User


class RecordStatus(PyEnum):
    """Enumeration for recording status."""

    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class Recording(Base):
    """Recording model."""

    __tablename__ = "recordings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False, default='vi')
    name: Mapped[str] = mapped_column(String, nullable=False, default='', server_default=text("''"))
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, name="record_status"), nullable=False, default=RecordStatus.PENDING)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recordings", passive_deletes=True)
    segments: Mapped[list["Segment"]] = relationship("Segment", back_populates="recording", cascade="all, delete-orphan", passive_deletes=True)
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="recording", cascade="all, delete-orphan", passive_deletes=True)
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship("TranscriptChunk", back_populates="recording", cascade="all, delete-orphan", passive_deletes=True)
