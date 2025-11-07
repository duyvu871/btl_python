"""
Use case for getting a recording with its segments.
"""
from uuid import UUID

from fastapi import Depends, HTTPException

from src.modules.record.schema import RecordingDetailResponse
from src.shared.uow import UnitOfWork, get_uow


class GetRecordingUseCase:
    """
    Use case for retrieving a recording with all its segments.

    This is called from REST API when user wants to view recording details.
    Validates ownership and loads segments.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, recording_id: UUID, user_id: UUID) -> RecordingDetailResponse:
        """
        Get a recording with segments for a user.

        Args:
            recording_id: Recording UUID
            user_id: User UUID (for ownership validation)

        Returns:
            RecordingDetailResponse with recording and segments

        Raises:
            HTTPException: If recording not found or doesn't belong to user
        """
        # Get recording with segments
        recording = await self.uow.recording_repo.get_by_id_with_segments(recording_id)

        if not recording:
            raise HTTPException(status_code=404, detail="Recording not found")

        # Validate ownership
        if recording.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Convert to response schema
        return RecordingDetailResponse.model_validate(recording)


def get_recording_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> GetRecordingUseCase:
    """Dependency injector for GetRecordingUseCase."""
    return GetRecordingUseCase(uow)
