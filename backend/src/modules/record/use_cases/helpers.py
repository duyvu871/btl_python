"""
Helper class for record use cases.
Provides convenient wrappers around use cases with dependency injection support.
"""
from typing import Any, Coroutine
from uuid import UUID

from fastapi import Depends

from src.modules.record.schema import (
    CompleteRecordingRequestSchema,
    CreateRecordingRequestSchema,
    ListRecordingsRequest,
    ListRecordingsResponse,
    RecordingDetailResponse,
    RecordingResponseSchema,
    UpdateStatusRequestSchema,
)
from src.modules.record.use_cases.complete_recording_use_case import CompleteRecordingUseCase
from src.modules.record.use_cases.create_recording_use_case import CreateRecordingUseCase
from src.modules.record.use_cases.generate_upload_url_use_case import GenerateUploadUrlUseCase, \
    GenerateUploadUrlUseCaseResult
from src.modules.record.use_cases.get_recording_use_case import GetRecordingUseCase
from src.modules.record.use_cases.list_recordings_use_case import ListRecordingsUseCase
from src.modules.record.use_cases.update_status_use_case import UpdateStatusUseCase
from src.shared.uow import UnitOfWork, get_uow


class RecordUseCase:
    """
    Helper class that wraps record use cases.
    Designed to be used with FastAPI dependency injection.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Initialize helper with unit of work.

        Args:
            uow: UnitOfWork instance
        """
        self.uow = uow
        self._create_recording_use_case = CreateRecordingUseCase(uow)
        self._complete_recording_use_case = CompleteRecordingUseCase(uow)
        self._update_status_use_case = UpdateStatusUseCase(uow)
        self._get_recording_use_case = GetRecordingUseCase(uow)
        self._generate_upload_url_use_case = GenerateUploadUrlUseCase(uow)
        self._list_recordings_use_case = ListRecordingsUseCase(uow)

    async def create_recording(self, request: CreateRecordingRequestSchema) -> RecordingResponseSchema:
        """
        Create a new recording.
        """
        return await self._create_recording_use_case.execute(request)

    async def complete_recording(self, request: CompleteRecordingRequestSchema) -> RecordingResponseSchema:
        """
        Complete a recording with transcription segments.
        """
        return await self._complete_recording_use_case.execute(request)

    async def update_status(self, recording_id: UUID, request: UpdateStatusRequestSchema) -> RecordingResponseSchema:
        """
        Update recording status.
        """
        return await self._update_status_use_case.execute(recording_id, request)

    async def get_recording(self, recording_id: UUID, user_id: UUID) -> RecordingDetailResponse:
        """
        Get a recording with segments for a user.
        """
        return await self._get_recording_use_case.execute(recording_id, user_id)

    async def list_recordings(self, user_id: UUID, request: ListRecordingsRequest) -> ListRecordingsResponse:
        """
        List recordings for a user with filters and pagination.
        """
        return await self._list_recordings_use_case.execute(user_id, request)

    async def generate_upload_url(
        self,
        recording_id: UUID,
        user_id: UUID,
        language: str,
        expire_seconds: int = 600,
        max_upload_bytes: int = 100 * 1024 * 1024,
    ) -> GenerateUploadUrlUseCaseResult:
        """
        Generate presigned upload URL for a recording.

        Args:
            recording_id: UUID of the recording
            user_id: UUID of the user who owns the recording
            language: Language code for the recording
            expire_seconds: URL expiration time in seconds (default: 600 = 10 minutes)
            max_upload_bytes: Maximum file size in bytes (default: 100 MB)

        Returns:
            Dictionary with upload_url, upload_fields, expires_in, and object_key
        """
        return await self._generate_upload_url_use_case.execute(
            recording_id=recording_id,
            user_id=user_id,
            language=language,
            expire_seconds=expire_seconds,
            max_upload_bytes=max_upload_bytes,
        )



def get_record_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> RecordUseCase:
    """
    FastAPI dependency to get RecordUseCase instance.

    Returns:
        RecordUseCase instance
    """
    return RecordUseCase(uow)
