from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.db import Base

if TYPE_CHECKING:
    from .recording import Recording


class TranscriptChunk(Base):
    """Transcript chunk model for RAG."""

    __tablename__ = "transcript_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    recording_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    recording: Mapped["Recording"] = relationship("Recording", back_populates="transcript_chunks")

    __table_args__ = (
        UniqueConstraint("recording_id", "chunk_index", name="unique_recording_chunk"),
    )

