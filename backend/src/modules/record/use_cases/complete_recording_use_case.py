"""
Use case for completing a recording with transcription segments.
"""
from datetime import datetime
from typing import Any

from fastapi import Depends

from src.modules.record.schema import CompleteRecordingRequestSchema, RecordingResponseSchema
from src.shared.uow import UnitOfWork, get_uow


class CompleteRecordingUseCase:
    """
    Use case for completing a recording with transcription results.

    This is called from gRPC when AI service finishes processing.
    Saves segments, updates status to 'done', and increments used seconds.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, request: CompleteRecordingRequestSchema) -> RecordingResponseSchema:
        """
        Complete a recording with transcription segments.

        Args:
            request: CompleteRecordingRequestSchema with recording_id, duration_ms, segments

        Returns:
            RecordingResponseSchema with updated recording details

        Raises:
            ValueError: If recording not found or not in processing status
        """
        # Validate recording exists and is in processing status
        recording = await self.uow.recording_repo.get_by_id_with_segments(request.recording_id)
        if not recording:
            raise ValueError(f"Recording {request.recording_id} not found")

        if recording.status != 'processing':
            raise ValueError(f"Recording {request.recording_id} is not in processing status")

        # Prepare segment data
        segments_data: list[dict[str, Any]] = []
        for segment in request.segments:
            segments_data.append({
                'recording_id': request.recording_id,
                'idx': segment.idx,
                'start_ms': segment.start_ms,
                'end_ms': segment.end_ms,
                'text': segment.text
            })

        # Bulk create segments
        if segments_data:
            await self.uow.segment_repo.bulk_create(segments_data)

        # Update recording status and duration
        await self.uow.recording_repo.update_status(
            recording_id=request.recording_id,
            status='done',
            duration_ms=request.duration_ms,
            completed_at=datetime.now(datetime.UTC)
        )

        # Update subscription used seconds
        await self.uow.subscription_repo.update_used_seconds(
            user_id=recording.user_id,
            seconds=request.duration_ms // 1000  # Convert ms to seconds
        )

        # Commit transaction
        await self.uow.commit()

        # Return updated recording info
        return RecordingResponseSchema(
            recording_id=recording.id,
            status='done',
            duration_ms=request.duration_ms
        )


def get_complete_recording_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> CompleteRecordingUseCase:
    """Dependency injector for CompleteRecordingUseCase."""
    return CompleteRecordingUseCase(uow)
