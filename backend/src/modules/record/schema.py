"""
Pydantic schemas for record module.
"""
from datetime import datetime
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
    created_at: datetime


# ============================================================================
# Recording Schemas
# ============================================================================

class RecordingBase(BaseModel):
    """Base schema for Recording."""
    source: str = Field(description="Source: 'realtime' or 'upload'")
    language: str = Field(description="Language code, e.g., 'vi', 'en'")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


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

class UploadRecordingRequest(BaseModel):
    """Request schema for uploading a recording file."""
    language: str = Field(description="Language code, e.g., 'vi', 'en'")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class CreateRealtimeRecordingRequest(BaseModel):
    """Request schema for creating a realtime recording."""
    language: str = Field(description="Language code, e.g., 'vi', 'en'")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


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


class QuotaResponse(BaseModel):
    """Response schema for quota check."""
    has_quota: bool
    error_message: str = ""


class RecordingResponseSchema(BaseModel):
    """Response schema for recording operations via gRPC."""
    recording_id: UUID
    status: str
    duration_ms: int


# ============================================================================
# Filter and Search Schemas
# ============================================================================

class RecordingFilters(BaseModel):
    """Schema for recording filters."""
    status: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchSegmentsRequest(BaseModel):
    """Request schema for searching segments."""
    query: str = Field(description="Search query")
    recording_id: UUID
