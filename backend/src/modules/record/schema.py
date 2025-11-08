"""
Pydantic schemas for record module.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Segment Schemas
# ============================================================================

class SegmentBase(BaseModel):
    """Base schema for Segment."""
    idx: int
    start_ms: int
    end_ms: int
    text: str


class SegmentResponse(BaseModel):
    """Response schema for Segment."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recording_id: UUID
    idx: int
    start_ms: int
    end_ms: int
    text: str


# ============================================================================
# Recording Schemas
# ============================================================================

class RecordingResponse(BaseModel):
    """Response schema for Recording."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source: str
    language: str
    status: str
    duration_ms: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None


class RecordingDetailResponse(BaseModel):
    """Detailed recording response with segments."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source: str
    language: str
    status: str
    duration_ms: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None
    segments: List[SegmentResponse] = Field(default_factory=list)


class RecordingStatsResponse(BaseModel):
    """Response schema for recording statistics."""
    total_recordings: int
    total_duration_ms: int
    total_duration_minutes: float
    completed_count: int
    processing_count: int
    failed_count: int


# ============================================================================
# Request Schemas for REST API
# ============================================================================

class UploadRecordingResponse(BaseModel):
    """Response schema for upload recording endpoint."""
    recording_id: UUID = Field(description="ID of the created recording")
    upload_url: str = Field(description="Presigned URL for uploading the audio file")
    expires_in: int = Field(default=3600, description="URL expiration time in seconds")

class SupportedLanguage(str, Enum):
    """Supported languages for transcription."""
    VIETNAMESE = "vi"
    ENGLISH = "en"

class UploadRecordingRequest(BaseModel):
    """Request schema for uploading a new recording."""
    # meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata to update")
    language: Optional[SupportedLanguage] = Field(default=SupportedLanguage.VIETNAMESE,
                                                  description="Language of the recording")

class UpdateRecordingRequest(BaseModel):
    """Request schema for updating recording metadata."""
    # meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata to update")
    language: Optional[SupportedLanguage] = Field(default=SupportedLanguage.VIETNAMESE, description="Language of the recording")


class DeleteRecordingResponse(BaseModel):
    """Response schema for delete recording endpoint."""
    recording_id: UUID
    message: str = "Recording deleted successfully"
    deleted_segments_count: int = 0


class ListRecordingsRequest(BaseModel):
    """Request schema for listing recordings with filters."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    status: Optional[str] = Field(default=None, description="Filter by status")
    source: Optional[str] = Field(default=None, description="Filter by source")
    language: Optional[str] = Field(default=None, description="Filter by language")


class ListRecordingsResponse(BaseModel):
    """Response schema for listing recordings."""
    recordings: List[RecordingResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SearchSegmentsRequest(BaseModel):
    """Request schema for searching segments."""
    query: str = Field(description="Search query")
    recording_id: Optional[UUID] = Field(default=None, description="Filter by specific recording")
    limit: int = Field(default=10, ge=1, le=100, description="Max results to return")


class SearchSegmentsResponse(BaseModel):
    """Response schema for segment search."""
    segments: List[SegmentResponse]
    total_matches: int
    query: str


class GetTranscriptResponse(BaseModel):
    """Response schema for transcript."""
    recording_id: UUID
    transcript: str = Field(description="Full transcript text or formatted content")
    format: str
    segment_count: int


# ============================================================================
# gRPC Request/Response Schemas
# ============================================================================

class CreateRecordingRequestSchema(BaseModel):
    """Schema for creating recording via gRPC."""
    user_id: UUID
    source: str
    language: str
    meta: Optional[Dict[str, Any]] = None


class CompleteRecordingRequestSchema(BaseModel):
    """Schema for completing recording via gRPC."""
    recording_id: UUID
    duration_ms: int
    segments: List[SegmentBase]


class UpdateStatusRequestSchema(BaseModel):
    """Schema for updating recording status via gRPC."""
    status: str
    error_message: Optional[str] = None


class RecordingResponseSchema(BaseModel):
    """Response schema for recording operations via gRPC."""
    recording_id: UUID
    status: str
    duration_ms: int



