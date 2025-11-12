"""
Repository layer for record module.
Handles database queries for Recording and Segment models.
"""
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models.plan import Plan
from src.core.database.models.recording import Recording, RecordStatus
from src.core.database.models.segment import Segment, SegmentWord
from src.core.database.models.user import User
from src.core.database.models.user_subscription import UserSubscription
from src.shared.base.base_repository import BaseRepository


class RecordingRepository(BaseRepository[Recording]):
    """
    Repository for Recording model.
    Manages CRUD operations and business queries for recordings.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Recording, session)

    async def get_by_id_with_segments(self, recording_id: UUID) -> Recording | None:
        """
        Get a recording by ID with all its segments and segment words loaded.

        Args:
            recording_id: Recording UUID

        Returns:
            Recording instance with segments and words loaded, or None if not found
        """
        query = (
            select(Recording)
            .options(
                selectinload(Recording.segments).selectinload(Segment.words)
            )
            .where(Recording.id == recording_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_user_recordings(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        filters: dict[str, Any] | None = None
    ) -> tuple[list[Recording], int]:
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
        status: RecordStatus,
        duration_ms: int | None = None,
        completed_at: datetime | None = None
    ) -> bool:
        """
        Update recording status and related fields.

        Args:
            recording_id: Recording UUID
            status: New status (RecordStatus enum)
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

    async def get_user_stats(self, user_id: UUID) -> dict[str, Any]:
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
                'usage_cycle': str,  # from plan billing_cycle
                'usage_minutes': float,  # current cycle usage in minutes
                'usage_count': int,  # current cycle recording count
                'quota_minutes': int,  # plan quota in minutes
                'quota_count': int,  # plan quota in number of recordings
                'average_recording_duration_ms': float,
                'completed_count': int,
                'processing_count': int,
                'failed_count': int
            }
        """

        # Get user with subscription and plan
        user_result = await self.session.execute(
            select(User)
            .options(
                selectinload(User.subscription).selectinload(UserSubscription.plan)
            )
            .where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        # Get subscription cycle info and quota
        usage_cycle = "MONTHLY"  # default
        usage_minutes = 0.0
        usage_count = 0
        quota_minutes = 0  # default for free/no plan
        quota_count = 0  # default for free/no plan

        if user and user.subscription:
            subscription = user.subscription
            if subscription.plan:
                plan = subscription.plan
                usage_cycle = plan.billing_cycle.value
                quota_minutes = plan.monthly_minutes
                quota_count = plan.monthly_usage_limit

            # Convert used_seconds to minutes
            usage_minutes = round(subscription.used_seconds / 60, 2)
            usage_count = subscription.usage_count

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

        # Total duration (all time)
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

        # Average recording duration
        total_recordings = sum(status_dict.values())
        average_duration_ms = 0.0
        if total_recordings > 0 and total_duration_ms > 0:
            average_duration_ms = round(total_duration_ms / total_recordings, 2)

        return {
            'total_recordings': total_recordings,
            'total_duration_ms': total_duration_ms,
            'total_duration_minutes': round(total_duration_ms / 60000, 2),  # ms to minutes
            'usage_cycle': usage_cycle,
            'usage_minutes': usage_minutes,
            'usage_count': usage_count,
            'quota_minutes': quota_minutes,
            'quota_count': quota_count,
            'average_recording_duration_ms': average_duration_ms,
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

    async def get_by_recording(self, recording_id: UUID) -> list[Segment]:
        """
        Get all segments for a recording with their words, ordered by index.

        Args:
            recording_id: Recording UUID

        Returns:
            List of Segment instances with words loaded
        """
        query = (
            select(Segment)
            .options(selectinload(Segment.words))
            .where(Segment.recording_id == recording_id)
            .order_by(Segment.idx)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def bulk_create(self, segments_data: list[dict[str, Any]]) -> list[Segment]:
        """
        Bulk create segments with their words for a recording.

        Args:
            segments_data: List of segment data dicts, each containing optional 'words' list

        Returns:
            List of created Segment instances with words
        """
        segments = []
        for seg_data in segments_data:
            # Extract words data if present
            words_data = seg_data.pop('words', [])

            # Create segment
            segment = Segment(**seg_data)

            # Create associated words
            if words_data:
                segment.words = [SegmentWord(**word_data) for word_data in words_data]

            segments.append(segment)

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

    async def search_segments(self, recording_id: UUID, query: str) -> list[Segment]:
        """
        Search segments containing the query text.

        Args:
            recording_id: Recording UUID
            query: Search query string

        Returns:
            List of matching Segment instances with words loaded
        """
        search_pattern = f'%{query}%'
        query_stmt = (
            select(Segment)
            .options(selectinload(Segment.words))
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


class SegmentWordRepository(BaseRepository[SegmentWord]):
    """
    Repository for SegmentWord model.
    Manages individual words within segments.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(SegmentWord, session)

    async def get_by_segment(self, segment_id: UUID) -> list[SegmentWord]:
        """
        Get all words for a segment, ordered by start time.

        Args:
            segment_id: Segment UUID

        Returns:
            List of SegmentWord instances
        """
        query = (
            select(SegmentWord)
            .where(SegmentWord.segment_id == segment_id)
            .order_by(SegmentWord.start_ms)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def bulk_create(self, words_data: list[dict[str, Any]]) -> list[SegmentWord]:
        """
        Bulk create words for segments.

        Args:
            words_data: List of word data dicts

        Returns:
            List of created SegmentWord instances
        """
        words = [SegmentWord(**data) for data in words_data]
        self.session.add_all(words)
        await self.session.commit()

        # Refresh to get IDs
        for word in words:
            await self.session.refresh(word)

        return words

