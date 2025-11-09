"""
Use case for creating a new recording.
"""

from fastapi import Depends

from src.modules.record.schema import CreateRecordingRequestSchema, RecordingResponseSchema
from src.shared.uow import UnitOfWork, get_uow


class CreateRecordingUseCase:
    """
    Use case for creating a new recording.

    This is called from gRPC when AI service starts processing.
    Creates recording with status='processing' and triggers usage increment.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, request: CreateRecordingRequestSchema) -> RecordingResponseSchema:
        """
        Create a new recording.

        Args:
            request: CreateRecordingRequestSchema with user_id, source, language, meta

        Returns:
            RecordingResponseSchema with recording details

        Note:
            This does NOT check quota - quota check happens before this call.
            Usage count is incremented via database trigger.
        """
        # Create recording data
        recording_data = {
            'user_id': request.user_id,
            'source': request.source,
            'language': request.language,
            'status': 'processing',
            'duration_ms': 0,  # Will be updated when completed
            'meta': request.meta or {}
        }

        # Create recording in database
        recording = await self.uow.recording_repo.create(recording_data)

        # Return response
        return RecordingResponseSchema(
            recording_id=recording.id,
            status=recording.status,
            duration_ms=recording.duration_ms
        )


def get_create_recording_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> CreateRecordingUseCase:
    """Dependency injector for CreateRecordingUseCase."""
    return CreateRecordingUseCase(uow)
