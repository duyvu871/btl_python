"""
API routing for record module.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from src.core.config.env import global_logger_name
from src.core.database.models.user import User
from src.core.security.user import get_current_user
from src.modules.record.schema import (
    RecordingDetailResponse,
    ListRecordingsRequest,
    ListRecordingsResponse,
    RecordingStatsResponse
)
from src.modules.record.use_cases import (
    GetRecordingUseCase,
    get_recording_usecase,
    ListRecordingsUseCase,
    get_list_recordings_usecase
)
from src.shared.schemas.response import SuccessResponse

logger = logging.getLogger(global_logger_name)

router = APIRouter(
    prefix="/recordings",
    tags=["recordings"],
)


@router.post("/upload", response_model=SuccessResponse[dict])
async def upload_recording(
    file: UploadFile = File(...),
    language: str = "vi",
    meta: str = None,
    current_user: User = Depends(get_current_user),
    # TODO: Add use cases for upload
):
    """
    Upload an audio file for transcription.
    
    This endpoint accepts audio files, validates quota, uploads to storage,
    creates a recording record, and queues it for processing.
    
    Args:
        file: Audio file upload
        language: Language code (default: 'vi')
        meta: Optional JSON metadata
        current_user: Current user
    Returns:
        Recording ID and upload URL
    """
    try:
        # TODO: Implement upload logic
        # 1. Check quota
        # 2. Upload to S3/MinIO
        # 3. Create recording (status='processing')
        # 4. Queue Celery job
        # 5. Return recording_id and upload_url
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Upload functionality not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error uploading recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload recording"
        )


@router.get("/{recording_id}", response_model=SuccessResponse[RecordingDetailResponse])
async def get_recording(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetRecordingUseCase = Depends(get_recording_usecase),
):
    """
    Get detailed information about a specific recording.
    
    Includes recording metadata and all transcription segments.
    Validates that the recording belongs to the current user.
    
    Args:
        recording_id: UUID of the recording
        current_user: Authenticated user
        use_case: GetRecordingUseCase instance
    Returns:
        RecordingDetailResponse with recording and segments
    """
    try:
        result = await use_case.execute(recording_id, current_user.id)
        return SuccessResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recording {recording_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recording"
        )


@router.get("/", response_model=SuccessResponse[ListRecordingsResponse])
async def list_recordings(
    page: int = 1,
    per_page: int = 20,
    status_filter: str = None,
    source: str = None,
    language: str = None,
    current_user: User = Depends(get_current_user),
    use_case: ListRecordingsUseCase = Depends(get_list_recordings_usecase),
):
    """
    List user's recordings with pagination and filters.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page (max 100)
        status_filter: Filter by status ('processing', 'done', 'failed')
        source: Filter by source ('realtime', 'upload')
        language: Filter by language
        current_user: Authenticated user
        use_case: ListRecordingsUseCase instance
        
    Returns:
        ListRecordingsResponse with recordings and pagination info
    """
    try:
        request = ListRecordingsRequest(
            page=page,
            per_page=min(per_page, 100),  # Cap at 100
            status=status_filter,
            source=source,
            language=language
        )
        
        result = await use_case.execute(current_user.id, request)
        return SuccessResponse(data=result)
        
    except Exception as e:
        logger.error(f"Error listing recordings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recordings"
        )


@router.get("/stats", response_model=SuccessResponse[RecordingStatsResponse])
async def get_recording_stats(
    current_user: User = Depends(get_current_user),
    # TODO: Add use case for stats
):
    """
    Get recording statistics for the current user.
    
    Returns total recordings, duration, and counts by status.
    """
    try:
        # TODO: Implement stats logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stats functionality not yet implemented"
        )
        
    except Exception as e:
        logger.error(f"Error getting recording stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recording statistics"
        )


@router.delete("/{recording_id}", response_model=SuccessResponse[dict])
async def delete_recording(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    # TODO: Add use case for deletion
):
    """
    Delete a recording and its segments.
    
    Only allows deletion of recordings owned by the current user.
    Completed recordings cannot be deleted (for audit purposes).
    
    Args:
        recording_id: UUID of the recording to delete
        current_user: Authenticated user
    Returns:
        Success message
    """
    try:
        # TODO: Implement delete logic
        # 1. Validate ownership
        # 2. Check status (only allow deleting failed recordings)
        # 3. Delete segments
        # 4. Delete recording
        # 5. Delete from storage if applicable
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Delete functionality not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recording {recording_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recording"
        )
