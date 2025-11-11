"""
ARQ Worker for processing audio transcription asynchronously via Redis queue.
"""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

import httpx
from arq.connections import RedisSettings
from mako.filters import url_escape

from src.core.config.env import env
from src.core.database.db import AsyncSessionLocal
from src.core.database.models.recording import RecordStatus
from src.core.redis.worker import get_redis_pool
from src.core.s3.minio.client import minio_client
from src.core.security.token import create_access_token
from src.modules.record.schema import CompleteRecordingRequestSchema, SegmentBase, SegmentWordBase
from src.modules.record.use_cases.complete_recording_use_case import CompleteRecordingUseCase
from src.shared.uow import UnitOfWork

logger = logging.getLogger(__name__)


async def transcribe_audio_task(ctx: dict[str, Any], recording_id: str, user_id: str) -> bool:
    """
    ARQ task to transcribe uploaded audio file.

    Args:
        ctx: ARQ context (contains redis pool and other info)
        recording_id: UUID of the recording to transcribe
        user_id: UUID of the user who owns the recording

    Returns:
        True if transcription completed successfully, False otherwise
    """

    try:
        recording_uuid = UUID(recording_id)
        user_uuid = UUID(user_id)

        logger.info(f"Starting transcription for recording {recording_id}")

        # 1. Get recording from database
        async with AsyncSessionLocal() as session:
            uow = UnitOfWork(session)
            user = await uow.user_repo.get(user_uuid)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            recording = await uow.recording_repo.get(recording_uuid)
            if not recording:
                logger.error(f"Recording {recording_id} not found")
                return False

            if recording.status != RecordStatus.PENDING:
                logger.warning(f"Recording {recording_id} is not in pending status: {recording.status}")
                return False

            # 2. Update status to processing
            await uow.recording_repo.update(recording_uuid, {"status": RecordStatus.PROCESSING})
            await uow.commit()

        # 3. Get presigned URL for the audio file
        object_key = f"{user_id}/recordings/{recording_id}.wav"
        url_expiry = 24 * 60 * 60  # 24 hours
        download_url = minio_client.get_presigned_url(object_key, expiration=url_expiry)

        # generate access token for auth validation
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

        logger.info(f"Generated download URL for {object_key}")

        # 4. Call S2T service to transcribe
        s2t_url = f"{env.S2T_API_HOST}/api/v1/transcribe"

        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minutes timeout
            response = await client.post(
                s2t_url,
                json={
                    "uri": download_url,
                    "recording_id": recording_id,
                    "language": recording.language,
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"S2T service returned error: {response.status_code} - {response.text}")

                # Update status to failed
                async with AsyncSessionLocal() as session:
                    uow = UnitOfWork(session)
                    await uow.recording_repo.update(
                        recording_uuid,
                        {
                            "status": RecordStatus.FAILED,
                            "meta": {
                                **(recording.meta or {}),
                                "error": f"Transcription failed: {response.text}"
                            }
                        }
                    )
                    await uow.commit()
                return False

            # 5. Parse and validate response
            response_data = response.json()
            logger.info(f"Transcription response received for recording {recording_id}")

            # Validate response has required structure
            if "data" not in response_data:
                logger.error("Invalid response format: missing 'data' field")
                async with AsyncSessionLocal() as session:
                    uow = UnitOfWork(session)
                    await uow.recording_repo.update(
                        recording_uuid,
                        {
                            "status": RecordStatus.FAILED,
                            "meta": {
                                **(recording.meta or {}),
                                "error": "Invalid response format from S2T service"
                            }
                        }
                    )
                    await uow.commit()
                return False

            transcribe_data = response_data["data"]

            # Convert duration from seconds to milliseconds
            duration_ms = int(transcribe_data.get("duration", 0) * 1000)

            # 6. Convert segments and words to the schema format
            segments = []
            for idx, segment in enumerate(transcribe_data.get("segments", [])):
                # Convert words from S2T format to SegmentWordBase format
                words = []
                for word_data in segment.get("words", []):
                    words.append(SegmentWordBase(
                        text=word_data.get("word", ""),
                        start_ms=int(word_data.get("start", 0) * 1000),  # seconds to ms
                        end_ms=int(word_data.get("end", 0) * 1000)  # seconds to ms
                    ))

                # Create segment with words
                segments.append(SegmentBase(
                    idx=idx,
                    start_ms=int(segment.get("start", 0) * 1000),  # seconds to ms
                    end_ms=int(segment.get("end", 0) * 1000),  # seconds to ms
                    text=segment.get("text", ""),
                    words=words
                ))

            # 7. Call CompleteRecordingUseCase to save segments and words
            async with AsyncSessionLocal() as session:
                uow = UnitOfWork(session)
                complete_use_case = CompleteRecordingUseCase(uow)

                complete_request = CompleteRecordingRequestSchema(
                    recording_id=recording_uuid,
                    duration_ms=duration_ms,
                    segments=segments
                )

                await complete_use_case.execute(complete_request)

            logger.info(f"Successfully saved {len(segments)} segments with words for recording {recording_id}")

        logger.info(f"Transcription completed successfully for recording {recording_id}")
        return True

    except Exception as e:
        logger.error(f"Error in transcribe_audio_task for recording {recording_id}: {e}", exc_info=True)

        # Try to update status to failed
        try:
            async with AsyncSessionLocal() as session:
                uow = UnitOfWork(session)
                await uow.recording_repo.update(
                    UUID(recording_id),
                    {
                        "status": RecordStatus.FAILED,
                        "meta": {"error": str(e)}
                    }
                )
                await uow.commit()
        except Exception as update_error:
            logger.error(f"Failed to update recording status: {update_error}")

        raise


async def startup(ctx: dict[str, Any]) -> None:
    """
    Worker startup function - runs when worker starts.
    """
    logger.info("ARQ Transcription worker starting up...")
    ctx["startup_complete"] = True


async def shutdown(ctx: dict[str, Any]) -> None:
    """
    Worker shutdown function - runs when worker stops.
    """
    logger.info("ARQ Transcription worker shutting down...")


class WorkerSettings:
    """
    ARQ Worker settings configuration for transcription tasks.
    """

    redis_settings = RedisSettings(
        host=env.REDIS_HOST,
        port=env.REDIS_PORT,
        database=env.REDIS_DB,
    )

    # Task functions available to the worker
    functions = [transcribe_audio_task]

    # Worker configuration
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = env.ARQ_MAX_JOBS
    job_timeout = 600  # 10 minutes for transcription
    queue_name = "arq:transcribe"  # Separate queue for transcription

    # Retry configuration
    max_tries = 2  # Retry once if failed
    retry_delay = 120  # Retry after 2 minutes


async def enqueue_transcription(recording_id: str, user_id: str) -> str | None:
    """
    Enqueue a transcription task to be processed by the worker.

    Args:
        recording_id: UUID string of the recording
        user_id: UUID string of the user

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        redis = await get_redis_pool()
        job = await redis.enqueue_job(
            "transcribe_audio_task",
            recording_id,
            user_id,
            _queue_name="arq:transcribe"
        )
        logger.info(f"Transcription job enqueued: {job.job_id} for recording {recording_id}")
        await redis.close()
        return job.job_id
    except Exception as e:
        logger.error(f"Failed to enqueue transcription job: {e}", exc_info=True)
        return None

