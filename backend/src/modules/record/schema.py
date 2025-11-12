"""
Pydantic schemas for record module.
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Segment Word Schemas
# ============================================================================

class SegmentWordBase(BaseModel):
    """Base schema for SegmentWord."""
    text: str
    start_ms: int
    end_ms: int


class SegmentWordResponse(BaseModel):
    """Response schema for SegmentWord."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    segment_id: UUID
    text: str
    start_ms: int
    end_ms: int


# ============================================================================
# Segment Schemas
# ============================================================================

class SegmentBase(BaseModel):
    """Base schema for Segment."""
    idx: int
    start_ms: int
    end_ms: int
    text: str
    words: list[SegmentWordBase] = Field(default_factory=list)


class SegmentResponse(BaseModel):
    """Response schema for Segment."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recording_id: UUID
    idx: int
    start_ms: int
    end_ms: int
    text: str
    words: list[SegmentWordResponse] = Field(default_factory=list)


# ============================================================================
# Recording Schemas
# ============================================================================

class RecordingResponse(BaseModel):
    """Response schema for Recording."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    source: str
    language: str
    status: str
    duration_ms: int
    created_at: datetime
    completed_at: datetime | None = None
    meta: dict[str, Any] | None = None


class RecordingDetailResponse(BaseModel):
    """Detailed recording response with segments."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    source: str
    language: str
    status: str
    duration_ms: int
    created_at: datetime
    completed_at: datetime | None = None
    meta: dict[str, Any] | None = None
    segments: list[SegmentResponse] = Field(default_factory=list)
    audio_url: str | None = Field(default=None, description="Presigned URL to download audio file")


class RecordingStatsResponse(BaseModel):
    """Response schema for recording statistics."""
    total_recordings: int
    total_duration_ms: int
    total_duration_minutes: float
    usage_cycle: str  # "MONTHLY" | "YEARLY" | "LIFETIME"
    usage_minutes: float  # this cycle usage in minutes
    usage_count: int  # this cycle usage in number of recordings
    quota_minutes: int  # plan quota in minutes (from plan.monthly_minutes)
    quota_count: int  # plan quota in number of recordings (from plan.monthly_recordings)
    average_recording_duration_ms: float
    completed_count: int
    processing_count: int
    failed_count: int


# ============================================================================
# Request Schemas for REST API
# ============================================================================

class UploadRecordingResponse(BaseModel):
    """Response schema for upload recording endpoint (presigned POST)."""
    recording_id: UUID = Field(description="ID of the created recording")
    upload_url: str = Field(description="Presigned form POST URL")
    upload_fields: dict[str, Any] = Field(description="Form fields that must be included when submitting the upload POST")
    expires_in: int = Field(default=3600, description="URL expiration time in seconds")


class RegenerateUploadUrlResponse(BaseModel):
    """Response schema for regenerating upload URL for existing recording."""
    recording_id: UUID = Field(description="ID of the recording")
    upload_url: str = Field(description="Presigned form POST URL")
    upload_fields: dict[str, Any] = Field(description="Form fields that must be included when submitting the upload POST")
    expires_in: int = Field(default=3600, description="URL expiration time in seconds")


class GetAudioUrlResponse(BaseModel):
    """Response schema for getting audio download/play URL."""
    recording_id: UUID = Field(description="ID of the recording")
    audio_url: str = Field(description="Presigned GET URL to access the audio file")
    expires_in: int = Field(default=3600, description="URL expiration time in seconds")
    file_name: str = Field(description="Audio file name")


class SupportedLanguage(str, Enum):
    """Supported languages for transcription."""
    VIETNAMESE = "vi"
    ENGLISH = "en"

class UploadRecordingRequest(BaseModel):
    """Request schema for uploading a new recording."""
    name: str | None = Field(default=None, description="Recording name (auto-generated if not provided)")
    language: SupportedLanguage | None = Field(default=SupportedLanguage.VIETNAMESE,
                                                  description="Language of the recording")

class UpdateRecordingRequest(BaseModel):
    """Request schema for updating recording metadata."""
    name: str | None = Field(default=None, description="Recording name")
    language: SupportedLanguage | None = Field(default=SupportedLanguage.VIETNAMESE, description="Language of the recording")


class DeleteRecordingResponse(BaseModel):
    """Response schema for delete recording endpoint."""
    recording_id: UUID
    message: str = "Recording deleted successfully"


class ListRecordingsRequest(BaseModel):
    """Request schema for listing recordings with filters."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    status: str | None = Field(default=None, description="Filter by status")
    source: str | None = Field(default=None, description="Filter by source")
    language: str | None = Field(default=None, description="Filter by language")


class ListRecordingsResponse(BaseModel):
    """Response schema for listing recordings."""
    recordings: list[RecordingResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SearchSegmentsRequest(BaseModel):
    """Request schema for searching segments."""
    query: str = Field(description="Search query")
    recording_id: UUID | None = Field(default=None, description="Filter by specific recording")
    limit: int = Field(default=10, ge=1, le=100, description="Max results to return")


class SearchSegmentsResponse(BaseModel):
    """Response schema for segment search."""
    segments: list[SegmentResponse]
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
    name: str | None = None
    meta: dict[str, Any] | None = None


class CompleteRecordingRequestSchema(BaseModel):
    """Schema for completing recording via gRPC."""
    recording_id: UUID
    duration_ms: int
    segments: list[SegmentBase]


class UpdateStatusRequestSchema(BaseModel):
    """Schema for updating recording status via gRPC."""
    status: str
    error_message: str | None = None


class RecordingResponseSchema(BaseModel):
    """Response schema for recording operations via gRPC."""
    recording_id: UUID
    status: str
    duration_ms: int


class MarkUploadCompletedRequest(BaseModel):
    """Request schema for marking upload as completed."""
    recording_id: UUID = Field(description="ID of the recording that was uploaded")


class MarkUploadCompletedResponse(BaseModel):
    """Response schema for marking upload as completed."""
    recording_id: UUID
    status: str
    message: str
    job_id: str | None = Field(default=None, description="Transcription job ID if queued successfully")
