"""
API routing for record module.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from src.core.config.env import global_logger_name
from src.core.database.models.recording import RecordStatus
from src.core.database.models.user import User
from src.core.security.user import get_current_user
from src.modules.record.schema import (
    RecordingDetailResponse,
    ListRecordingsRequest,
    ListRecordingsResponse,
    RecordingStatsResponse
)
from src.modules.record.use_cases import (
    RecordUseCase,
    get_record_usecase
)
from src.modules.subscription.use_cases.helpers import SubscriptionUseCase, get_subscription_usecase
from src.core.s3.minio.client import minio_client
from src.shared.uow import UnitOfWork, get_uow
from src.shared.schemas.response import SuccessResponse

logger = logging.getLogger(global_logger_name)

router = APIRouter(
    prefix="/record",
    tags=["record"],
)


@router.post("/upload", response_model=SuccessResponse[dict])
async def upload_recording(
    language: str = "vi",
    current_user: User = Depends(get_current_user),
    subscription_uc: SubscriptionUseCase = Depends(get_subscription_usecase),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Upload an audio file for transcription.
    
    This endpoint accepts audio files, validates quota, uploads to storage,
    creates a recording record, and queues it for processing.
    
    Args:
        language: Language code (default: 'vi')
        current_user: Current user
        subscription_uc: SubscriptionUseCase instance
        uow: UnitOfWork instance
    Returns:
        Recording ID and upload URL
    """
    try:
        # 1. Check quota
        has_quota, error_msg = await subscription_uc.check_quota(current_user.id)
        if not has_quota:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # 2. Ensure MinIO bucket exists
        minio_client.create_bucket()

        # 3. Create recording record with status 'processing'
        recording_data = {
            'user_id': current_user.id,
            'source': 'upload',
            'language': language,
            'status': RecordStatus.PENDING,
            'duration_ms': 0,
            'meta': {}
        }
        recording = await uow.recording_repo.create(recording_data)

        # 4. Generate presigned URL for upload
        object_key = f"{current_user.id}/recordings/{recording.id}.wav"
        upload_url = minio_client.client.generate_presigned_url(
            'put_object',
            Params={'Bucket': minio_client.bucket_name, 'Key': object_key},
            ExpiresIn=3600  # 1 hour
        )

        # 5. Return recording ID and upload URL
        return SuccessResponse(data={
            "recording_id": str(recording.id),
            "upload_url": upload_url
        })

    except HTTPException:
        raise
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
    use_case: RecordUseCase = Depends(get_record_usecase),
):
    """
    Get detailed information about a specific recording.
    
    Includes recording metadata and all transcription segments.
    Validates that the recording belongs to the current user.
    
    Args:
        recording_id: UUID of the recording
        current_user: Authenticated user
        use_case: RecordUseCase instance
    Returns:
        RecordingDetailResponse with recording and segments
    """
    try:
        result = await use_case.get_recording(recording_id, current_user.id)
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
    use_case: RecordUseCase = Depends(get_record_usecase),
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
        use_case: RecordUseCase instance

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
        
        result = await use_case.list_recordings(current_user.id, request)
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
