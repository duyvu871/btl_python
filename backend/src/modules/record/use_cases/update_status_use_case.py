"""
Use case for updating recording status (typically for failures).
"""
from uuid import UUID
from datetime import datetime

from fastapi import Depends

from src.modules.record.schema import UpdateStatusRequestSchema, RecordingResponseSchema
from src.shared.uow import UnitOfWork, get_uow


class UpdateStatusUseCase:
    """
    Use case for updating recording status.

    This is called from gRPC when AI service encounters an error.
    Updates status to 'failed' and saves error message, but does NOT charge user.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, recording_id: UUID, request: UpdateStatusRequestSchema) -> RecordingResponseSchema:
        """
        Update recording status.

        Args:
            recording_id: Recording UUID
            request: UpdateStatusRequestSchema with status and error_message

        Returns:
            RecordingResponseSchema with updated recording details

        Note:
            This does NOT update used_seconds - failed recordings don't count against quota.
        """
        # Get current recording
        recording = await self.uow.recording_repo.get_by_id_with_segments(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        # Update status
        success = await self.uow.recording_repo.update_status(
            recording_id=recording_id,
            status=request.status,
            completed_at=datetime.now(datetime.UTC) if request.status in ['done', 'failed'] else None
        )

        if not success:
            raise ValueError(f"Failed to update recording {recording_id}")

        # If status is 'failed', save error message in meta
        if request.status == 'failed' and request.error_message:
            # Update meta with error
            meta = recording.meta or {}
            meta['error'] = request.error_message
            recording.meta = meta
            await self.uow.commit()

        # Return updated recording info
        return RecordingResponseSchema(
            recording_id=recording.id,
            status=request.status,
            duration_ms=recording.duration_ms
        )


def get_update_status_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> UpdateStatusUseCase:
    """Dependency injector for UpdateStatusUseCase."""
    return UpdateStatusUseCase(uow)
