from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.core.database.db import Base

if TYPE_CHECKING:
    from .user import User
    from .segment import Segment
    from .transcript_chunk import TranscriptChunk


class Recording(Base):
    """Recording model."""

    __tablename__ = "recordings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False, default='vi')
    status: Mapped[str] = mapped_column(String, nullable=False, default='processing')
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recordings")
    segments: Mapped[list["Segment"]] = relationship("Segment", back_populates="recording")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship("TranscriptChunk", back_populates="recording")
