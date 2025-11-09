"""
Use case for listing recordings with pagination and filters.
"""
from math import ceil
from typing import Any
from uuid import UUID

from fastapi import Depends

from src.modules.record.schema import ListRecordingsRequest, ListRecordingsResponse, RecordingResponse
from src.shared.uow import UnitOfWork, get_uow


class ListRecordingsUseCase:
    """
    Use case for listing user recordings with pagination and filters.

    This is called from REST API for dashboard and recording management.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        request: ListRecordingsRequest
    ) -> ListRecordingsResponse:
        """
        List recordings for a user with filters and pagination.

        Args:
            user_id: User UUID
            request: ListRecordingsRequest with pagination and filters

        Returns:
            ListRecordingsResponse with recordings and pagination info
        """
        # Prepare filters
        filters: dict[str, Any] = {}
        if request.status:
            filters['status'] = request.status
        if request.source:
            filters['source'] = request.source
        if request.language:
            filters['language'] = request.language

        # Get recordings with pagination
        recordings, total = await self.uow.recording_repo.list_user_recordings(
            user_id=user_id,
            page=request.page,
            per_page=request.per_page,
            filters=filters if filters else None
        )

        # Calculate pagination info
        total_pages = ceil(total / request.per_page) if total > 0 else 0

        # Convert to response schemas
        recording_responses = [
            RecordingResponse.model_validate(recording)
            for recording in recordings
        ]

        return ListRecordingsResponse(
            recordings=recording_responses,
            total=total,
            page=request.page,
            per_page=request.per_page,
            total_pages=total_pages
        )


def get_list_recordings_usecase(
    uow: UnitOfWork = Depends(get_uow),
) -> ListRecordingsUseCase:
    """Dependency injector for ListRecordingsUseCase."""
    return ListRecordingsUseCase(uow)
