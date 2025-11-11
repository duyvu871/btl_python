"""
Helper utilities for working with transcription worker queue.
"""

import logging
from uuid import UUID

from src.workers.transcribe import enqueue_transcription

logger = logging.getLogger(__name__)


async def queue_transcription(recording_id: UUID, user_id: UUID) -> str | None:
    return await enqueue_transcription(str(recording_id), str(user_id))

