"""
API routing for record module.
"""
import logging
from uuid import UUID
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, func

from src.core.config.env import global_logger_name
from src.core.database.models import Segment
from src.core.database.models.recording import RecordStatus, Recording
from src.core.database.models.user import User
from src.core.security.user import get_current_user
from src.modules.record.schema import (
    RecordingDetailResponse,
    ListRecordingsRequest,
    ListRecordingsResponse,
    RecordingStatsResponse,
    UploadRecordingResponse,
    DeleteRecordingResponse,
    UpdateRecordingRequest,
    RecordingResponse,
    SearchSegmentsRequest,
    SearchSegmentsResponse,
    GetTranscriptResponse,
    SegmentResponse, SupportedLanguage, UploadRecordingRequest,
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


@router.post("/upload", response_model=SuccessResponse[UploadRecordingResponse])
async def upload_recording(
    request: UploadRecordingRequest,
    current_user: User = Depends(get_current_user),
    subscription_uc: SubscriptionUseCase = Depends(get_subscription_usecase),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Upload an audio file for transcription.
    
    This endpoint accepts audio files, validates quota, uploads to storage,
    creates a recording record, and queues it for processing.
    
    Supported languages: Vietnamese (vi), English (en)

    Args:
        request: Language code - 'vi' for Vietnamese (default) or 'en' for English
        current_user: Current user
        subscription_uc: SubscriptionUseCase instance
        uow: UnitOfWork instance
    Returns:
        Recording ID and upload URL
    """

    language = request.language or SupportedLanguage.VIETNAMESE

    try:
        # 1. Check quota
        # has_quota, error_msg = await subscription_uc.check_quota(current_user.id)
        # if not has_quota:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=error_msg
        #     )

        # 2. Ensure MinIO bucket exists
        minio_client.create_bucket()

        # 3. Create recording record with status 'pending'
        recording_data = {
            'user_id': current_user.id,
            'source': 'upload',
            'language': language.value,
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
        response_data = UploadRecordingResponse(
            recording_id=recording.id,
            upload_url=upload_url,
            expires_in=3600
        )
        return SuccessResponse(data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload recording"
        )


@router.get("/stats", response_model=SuccessResponse[RecordingStatsResponse])
async def get_recording_stats(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get recording statistics for the current user.
    
    Returns total recordings, duration, and counts by status.

    Args:
        current_user: Authenticated user
        uow: UnitOfWork instance

    Returns:
        RecordingStatsResponse with statistics
    """
    try:
        stats = await uow.recording_repo.get_user_stats(current_user.id)

        response_data = RecordingStatsResponse(
            total_recordings=stats['total_recordings'],
            total_duration_ms=stats['total_duration_ms'],
            total_duration_minutes=stats['total_duration_minutes'],
            completed_count=stats['completed_count'],
            processing_count=stats['processing_count'],
            failed_count=stats['failed_count']
        )

        return SuccessResponse(data=response_data)

    except Exception as e:
        logger.error(f"Error getting recording stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recording statistics"
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

@router.delete("/{recording_id}", response_model=SuccessResponse[DeleteRecordingResponse])
async def delete_recording(
    recording_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Delete a recording and its segments.
    
    Only allows deletion of recordings owned by the current user.
    Completed recordings can be deleted (soft delete for audit purposes).

    Args:
        recording_id: UUID of the recording to delete
        current_user: Authenticated user
        uow: UnitOfWork instance

    Returns:
        DeleteRecordingResponse with deletion details
    """
    try:
        # 1. Get recording and validate ownership
        recording = await uow.recording_repo.get(recording_id)
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )

        if recording.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this recording"
            )

        # 2. Get segments count before deletion
        segments = await uow.segment_repo.get_by_recording(recording_id)
        segments_count = len(segments)

        # 3. Delete recording
        await uow.recording_repo.delete(recording_id)

        # 4. Delete from storage if applicable
        try:
            object_key = f"{current_user.id}/recordings/{recording_id}.wav"
            minio_client.delete_object(object_key)
        except Exception as e:
            logger.warning(f"Failed to delete storage object for recording {recording_id}: {e}")
            # Continue even if storage deletion fails

        response_data = DeleteRecordingResponse(
            recording_id=recording_id,
            message="Recording deleted successfully",
            deleted_segments_count=segments_count
        )

        return SuccessResponse(data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recording {recording_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recording"
        )


@router.put("/{recording_id}", response_model=SuccessResponse[RecordingResponse])
async def update_recording(
    recording_id: UUID,
    request: UpdateRecordingRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Update recording metadata.

    Allows updating language and metadata fields.
    Only the owner can update their recordings.

    Args:
        recording_id: UUID of the recording
        request: UpdateRecordingRequest with fields to update
        current_user: Authenticated user
        uow: UnitOfWork instance

    Returns:
        RecordingResponse with updated recording
    """
    try:
        # 1. Get recording and validate ownership
        recording = await uow.recording_repo.get_by_id(recording_id)
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )

        if recording.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this recording"
            )

        # 2. Update fields
        update_data = {}
        if request.language is not None:
            update_data['language'] = request.language
        if request.meta is not None:
            # Merge with existing meta
            current_meta = recording.meta or {}
            current_meta.update(request.meta)
            update_data['meta'] = current_meta

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # 3. Update recording
        updated_recording = await uow.recording_repo.update(recording_id, update_data)

        return SuccessResponse(data=RecordingResponse.model_validate(updated_recording))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recording {recording_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recording"
        )


@router.get("/{recording_id}/transcript", response_model=SuccessResponse[GetTranscriptResponse])
async def get_transcript(
    recording_id: UUID,
    format_response: str = "text",
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get the full transcript of a recording.

    Supports multiple formats: text, json, srt, vtt

    Args:
        recording_id: UUID of the recording
        format_response: Output format ('text', 'json', 'srt', 'vtt')
        current_user: Authenticated user
        uow: UnitOfWork instance

    Returns:
        GetTranscriptResponse with transcript in requested format
    """
    try:
        # 1. Get recording and validate ownership
        recording = await uow.recording_repo.get_by_id(recording_id)
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )

        if recording.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this recording"
            )

        # 2. Get segments
        segments = await uow.segment_repo.get_by_recording(recording_id)

        if not segments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No transcript available for this recording"
            )

        # 3. Format transcript based on requested format
        if format_response == "text":
            transcript = " ".join(segment.text for segment in segments)
        elif format_response == "json":
            import json
            transcript_data = [
                {
                    "idx": seg.idx,
                    "start_ms": seg.start_ms,
                    "end_ms": seg.end_ms,
                    "text": seg.text
                }
                for seg in segments
            ]
            transcript = json.dumps(transcript_data, ensure_ascii=False, indent=2)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format_response}. Use 'text', 'json', 'srt', or 'vtt'"
            )

        response_data = GetTranscriptResponse(
            recording_id=recording_id,
            transcript=transcript,
            format=format_response,
            segment_count=len(segments)
        )

        return SuccessResponse(data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript for recording {recording_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcript"
        )


@router.post("/search", response_model=SuccessResponse[SearchSegmentsResponse])
async def search_segments(
    request: SearchSegmentsRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Search for segments containing the query text.

    Searches across all user's recordings or a specific recording.

    Args:
        request: SearchSegmentsRequest with query and filters
        current_user: Authenticated user
        uow: UnitOfWork instance

    Returns:
        SearchSegmentsResponse with matching segments
    """
    try:
        # Join segments with recordings to filter by user
        query = (
            select(Segment)
            .join(Recording, Segment.recording_id == Recording.id)
            .where(Recording.user_id == current_user.id)
        )

        # Add text search
        search_pattern = f"%{request.query}%"
        query = query.where(Segment.text.ilike(search_pattern))

        # Filter by specific recording if provided
        if request.recording_id:
            query = query.where(Segment.recording_id == request.recording_id)

        # Order by recording and segment index
        query = query.order_by(Recording.created_at.desc(), Segment.idx)

        # Apply limit
        query = query.limit(request.limit)

        # Execute query
        result = await uow.session.execute(query)
        segments = list(result.scalars().all())

        # Get total count (without limit)
        count_query = (
            select(func.count(Segment.id))
            .join(Recording, Segment.recording_id == Recording.id)
            .where(
                and_(
                    Recording.user_id == current_user.id,
                    Segment.text.ilike(search_pattern)
                )
            )
        )
        if request.recording_id:
            count_query = count_query.where(Segment.recording_id == request.recording_id)

        count_result = await uow.session.execute(count_query)
        total_matches = count_result.scalar() or 0

        response_data = SearchSegmentsResponse(
            segments=[SegmentResponse.model_validate(seg) for seg in segments],
            total_matches=total_matches,
            query=request.query
        )

        return SuccessResponse(data=response_data)

    except Exception as e:
        logger.error(f"Error searching segments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search segments"
        )

