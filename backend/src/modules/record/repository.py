"""
Repository layer for record module.
Handles database queries for Recording and Segment models.
"""
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models.recording import Recording, RecordStatus
from src.core.database.models.segment import Segment
from src.shared.base.base_repository import BaseRepository


class RecordingRepository(BaseRepository[Recording]):
    """
    Repository for Recording model.
    Manages CRUD operations and business queries for recordings.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Recording, session)

    async def get_by_id_with_segments(self, recording_id: UUID) -> Optional[Recording]:
        """
        Get a recording by ID with all its segments loaded.

        Args:
            recording_id: Recording UUID

        Returns:
            Recording instance with segments loaded, or None if not found
        """
        query = (
            select(Recording)
            .options(selectinload(Recording.segments))
            .where(Recording.id == recording_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_user_recordings(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Recording], int]:
        """
        List recordings for a user with pagination and filters.

        Args:
            user_id: User UUID
            page: Page number (1-based)
            per_page: Items per page
            filters: Optional filters dict (status, source, etc.)

        Returns:
            Tuple of (recordings list, total count)
        """
        query = select(Recording).where(Recording.user_id == user_id)

        # Apply filters
        if filters:
            if 'status' in filters:
                query = query.where(Recording.status == filters['status'])
            if 'source' in filters:
                query = query.where(Recording.source == filters['source'])
            if 'language' in filters:
                query = query.where(Recording.language == filters['language'])

        # Get total count
        count_query = query.with_only_columns(func.count()).order_by(None)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * per_page
        query = query.order_by(Recording.created_at.desc()).offset(offset).limit(per_page)

        result = await self.session.execute(query)
        recordings = list(result.scalars().all())

        return recordings, total

    async def update_status(
        self,
        recording_id: UUID,
        status: str,
        duration_ms: Optional[int] = None,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update recording status and related fields.

        Args:
            recording_id: Recording UUID
            status: New status ('processing', 'done', 'failed')
            duration_ms: Duration in milliseconds (for completion)
            completed_at: Completion timestamp

        Returns:
            True if updated, False if not found
        """
        query = select(Recording).where(Recording.id == recording_id)
        result = await self.session.execute(query)
        recording = result.scalars().first()

        if not recording:
            return False

        recording.status = status
        if duration_ms is not None:
            recording.duration_ms = duration_ms
        if completed_at is not None:
            recording.completed_at = completed_at

        await self.session.commit()
        return True

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get recording statistics for a user.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with stats:
            {
                'total_recordings': int,
                'total_duration_ms': int,
                'total_duration_minutes': float,
                'completed_count': int,
                'processing_count': int,
                'failed_count': int
            }
        """
        # Count by status
        status_counts = await self.session.execute(
            select(
                Recording.status,
                func.count(Recording.id).label('count')
            )
            .where(Recording.user_id == user_id)
            .group_by(Recording.status)
        )

        status_dict = {row.status: row.count for row in status_counts}

        # Total duration
        duration_result = await self.session.execute(
            select(func.sum(Recording.duration_ms))
            .where(
                and_(
                    Recording.user_id == user_id,
                    Recording.status == RecordStatus.COMPLETED
                )
            )
        )
        total_duration_ms = duration_result.scalar() or 0

        return {
            'total_recordings': sum(status_dict.values()),
            'total_duration_ms': total_duration_ms,
            'total_duration_minutes': round(total_duration_ms / 60000, 2),  # ms to minutes
            'completed_count': status_dict.get('completed', 0),
            'processing_count': status_dict.get('processing', 0),
            'failed_count': status_dict.get('failed', 0)
        }


class SegmentRepository(BaseRepository[Segment]):
    """
    Repository for Segment model.
    Manages transcription segments for recordings.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Segment, session)

    async def get_by_recording(self, recording_id: UUID) -> List[Segment]:
        """
        Get all segments for a recording, ordered by index.

        Args:
            recording_id: Recording UUID

        Returns:
            List of Segment instances
        """
        query = (
            select(Segment)
            .where(Segment.recording_id == recording_id)
            .order_by(Segment.idx)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def bulk_create(self, segments_data: List[Dict[str, Any]]) -> List[Segment]:
        """
        Bulk create segments for a recording.

        Args:
            segments_data: List of segment data dicts

        Returns:
            List of created Segment instances
        """
        segments = [Segment(**data) for data in segments_data]
        self.session.add_all(segments)
        await self.session.commit()

        # Refresh to get IDs
        for segment in segments:
            await self.session.refresh(segment)

        return segments

    async def get_transcript_text(self, recording_id: UUID) -> str:
        """
        Get the full transcript text for a recording.

        Args:
            recording_id: Recording UUID

        Returns:
            Concatenated transcript text
        """
        segments = await self.get_by_recording(recording_id)
        return ' '.join(segment.text for segment in segments)

    async def search_segments(self, recording_id: UUID, query: str) -> List[Segment]:
        """
        Search segments containing the query text.

        Args:
            recording_id: Recording UUID
            query: Search query string

        Returns:
            List of matching Segment instances
        """
        search_pattern = f'%{query}%'
        query_stmt = (
            select(Segment)
            .where(
                and_(
                    Segment.recording_id == recording_id,
                    func.lower(Segment.text).like(func.lower(search_pattern))
                )
            )
            .order_by(Segment.idx)
        )
        result = await self.session.execute(query_stmt)
        return list(result.scalars().all())
