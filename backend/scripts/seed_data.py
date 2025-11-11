"""
Script to seed initial data into the database, but not create admin user.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.core.database.db import get_db
from src.core.database.models import Plan, Recording, Segment, SegmentWord, TranscriptChunk, User, UserProfile, UserSubscription
from src.core.database.models.plan import BillingCycle, PlanType
from src.core.database.models.recording import RecordStatus
from src.core.database.models.user import Role, UserStatus
from src.core.security.password import hash_password

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def seed_plans(db):
    """Seed initial plans."""
    logger.info("Seeding plans...")
    plans_data = [
        {
            "code": "free",
            "name": "Free Plan",
            "description": "Basic free plan with limited features",
            "plan_type": PlanType.FREE,
            "billing_cycle": BillingCycle.MONTHLY,
            "plan_cost": 0,
            "plan_discount": 0,
            "monthly_minutes": 60,
            "monthly_usage_limit": 10,
        },
        {
            "code": "basic",
            "name": "Basic Plan",
            "description": "Basic plan with more minutes",
            "plan_type": PlanType.BASIC,
            "billing_cycle": BillingCycle.MONTHLY,
            "plan_cost": 50000,
            "plan_discount": 0,
            "monthly_minutes": 300,
            "monthly_usage_limit": 50,
        },
        {
            "code": "premium",
            "name": "Premium Plan",
            "description": "Premium plan with unlimited usage",
            "plan_type": PlanType.PREMIUM,
            "billing_cycle": BillingCycle.MONTHLY,
            "plan_cost": 100000,
            "plan_discount": 0,
            "monthly_minutes": 1000,
            "monthly_usage_limit": 200,
        },
        {
            "code": "enterprise",
            "name": "Enterprise Plan",
            "description": "Enterprise plan for large organizations",
            "plan_type": PlanType.ENTERPRISE,
            "billing_cycle": BillingCycle.YEARLY,
            "plan_cost": 500000,
            "plan_discount": 0,
            "monthly_minutes": 5000,
            "monthly_usage_limit": 1000,
        },
    ]
    count = 0
    for plan_data in plans_data:
        existing = (await db.execute(select(Plan).where(Plan.code == plan_data["code"]))).scalar()
        if not existing:
            plan = Plan(**plan_data)
            db.add(plan)
            count += 1
    await db.commit()
    logger.info(f"Seeded {count} plans")

async def seed_users(db):
    """Seed initial users."""
    logger.info("Seeding users...")
    users_data = [
        {
            "user_name": "testuser1",
            "email": "test1@example.com",
            "password": "password123",
            "role": Role.USER,
            "status": UserStatus.ACTIVE,
            "verified": True,
        },
        {
            "user_name": "testuser2",
            "email": "test2@example.com",
            "password": "password123",
            "role": Role.USER,
            "status": UserStatus.ACTIVE,
            "verified": True,
        },
        {
            "user_name": "testuser3",
            "email": "test3@example.com",
            "password": "password123",
            "role": Role.USER,
            "status": UserStatus.ACTIVE,
            "verified": False,
        },
    ]
    count = 0
    for user_data in users_data:
        existing = (await db.execute(select(User).where(User.email == user_data["email"]))).scalar()
        if not existing:
            user_data["password"] = hash_password(user_data["password"])
            user = User(**user_data)
            db.add(user)
            count += 1
    await db.commit()
    logger.info(f"Seeded {count} users")

async def seed_user_profiles(db):
    """Seed user profiles."""
    logger.info("Seeding user profiles...")
    users = (await db.execute(select(User))).scalars().all()
    count = 0
    for user in users:
        existing = (await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))).scalar()
        if not existing:
            profile = UserProfile(user_id=user.id, name=f"Profile for {user.user_name}")
            db.add(profile)
            count += 1
    await db.commit()
    logger.info(f"Seeded {count} user profiles")

async def seed_user_subscriptions(db):
    """Seed user subscriptions."""
    logger.info("Seeding user subscriptions...")
    users = (await db.execute(select(User))).scalars().all()
    plans = (await db.execute(select(Plan))).scalars().all()
    plan_dict = {plan.code: plan for plan in plans}
    count = 0
    for user in users:
        existing = (await db.execute(select(UserSubscription).where(UserSubscription.user_id == user.id))).scalar()
        if not existing:
            # Assign free plan by default
            plan = plan_dict.get("free")
            if plan:
                subscription = UserSubscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    cycle_start=datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                    cycle_end=datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=30),
                    usage_count=0,
                    used_seconds=0,
                )
                db.add(subscription)
                count += 1
    await db.commit()
    logger.info(f"Seeded {count} user subscriptions")

async def seed_recordings(db):
    """Seed recordings."""
    logger.info("Seeding recordings...")
    users = (await db.execute(select(User))).scalars().all()
    recordings_data = [
        {
            "source": "audio1.wav",
            "language": "vi",
            "status": RecordStatus.COMPLETED,
            "duration_ms": 60000,
            "completed_at": datetime.now(),
            "meta": {"quality": "high"},
        },
        {
            "source": "audio2.wav",
            "language": "en",
            "status": RecordStatus.COMPLETED,
            "duration_ms": 45000,
            "completed_at": datetime.now(),
            "meta": {"quality": "medium"},
        },
        {
            "source": "audio3.wav",
            "language": "vi",
            "status": RecordStatus.PROCESSING,
            "duration_ms": 0,
            "meta": {},
        },
    ]
    count = 0
    for i, rec_data in enumerate(recordings_data):
        user = users[i % len(users)]
        recording = Recording(user_id=user.id, **rec_data)
        db.add(recording)
        count += 1
        await db.flush()  # To get id
        # Seed segments and chunks for completed recordings
        if rec_data["status"] == RecordStatus.COMPLETED:
            await seed_segments_for_recording(db, recording.id, rec_data["duration_ms"])
            await seed_transcript_chunks_for_recording(db, recording.id, rec_data["duration_ms"])
    await db.commit()
    logger.info(f"Seeded {count} recordings")

async def seed_segments_for_recording(db, recording_id, duration_ms):
    """Seed segments for a recording."""
    num_segments = 5
    segment_duration = duration_ms // num_segments

    # Sample segment texts with corresponding words
    segment_texts = [
        "This is the first segment of the transcription.",
        "Here is the second part with different content.",
        "And finally the last segment completes the audio.",
        "Another example of what we can transcribe here.",
        "The final segment with some closing remarks.",
    ]

    for i in range(num_segments):
        segment_text = segment_texts[i] if i < len(segment_texts) else f"Sample text for segment {i + 1}."
        segment = Segment(
            recording_id=recording_id,
            idx=i,
            start_ms=i * segment_duration,
            end_ms=(i + 1) * segment_duration,
            text=segment_text,
        )
        db.add(segment)
        await db.flush()  # Get segment ID

        # Seed words for this segment
        await seed_segment_words(db, segment.id, segment.start_ms, segment.end_ms, segment_text)


async def seed_segment_words(db, segment_id, segment_start_ms, segment_end_ms, segment_text):
    """Seed individual words for a segment with timestamps."""
    words = segment_text.replace(",", "").replace(".", "").split()
    num_words = len(words)

    if num_words == 0:
        return

    segment_duration = segment_end_ms - segment_start_ms
    avg_word_duration = segment_duration // num_words

    current_time = segment_start_ms

    for i, word in enumerate(words):
        # Calculate word duration (with some variation)
        word_duration = int(avg_word_duration * (0.8 + 0.4 * (i % 3) / 3))

        # Ensure we don't exceed segment end
        word_end = min(current_time + word_duration, segment_end_ms)

        segment_word = SegmentWord(
            segment_id=segment_id,
            text=word,
            start_ms=current_time,
            end_ms=word_end,
        )
        db.add(segment_word)

        current_time = word_end

async def seed_transcript_chunks_for_recording(db, recording_id, duration_ms):
    """Seed transcript chunks for a recording."""
    num_chunks = 3
    chunk_duration = duration_ms // num_chunks
    for i in range(num_chunks):
        chunk = TranscriptChunk(
            recording_id=recording_id,
            chunk_index=i,
            start_ms=i * chunk_duration,
            end_ms=(i + 1) * chunk_duration,
            text=f"Sample chunk text {i + 1}.",
            token_count=10,
        )
        db.add(chunk)

async def seed_data():
    """Main seed function."""
    async for db in get_db():
        logger.info("Starting data seeding...")
        await seed_plans(db)
        await seed_users(db)
        await seed_user_profiles(db)
        await seed_user_subscriptions(db)
        await seed_recordings(db)

async def seed_admin():
    """Create or update admin user from environment variables."""

    return None


if __name__ == "__main__":
    asyncio.run(seed_data())
