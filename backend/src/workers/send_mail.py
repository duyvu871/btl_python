"""
ARQ Worker for sending emails asynchronously via Redis queue.
"""

import logging
from typing import Any

from arq.connections import RedisSettings

from src.core.config.env import env
from src.core.redis.worker import get_redis_pool
from src.modules.email.service import email_service
from src.modules.email.use_cases import (
    SendPasswordResetEmailRequest,
    SendPasswordResetEmailUseCase,
    SendVerificationEmailRequest,
    SendVerificationEmailUseCase,
)
from src.shared.schemas.email import CustomEmailTask, EmailType, PasswordResetEmailTask, VerificationEmailTask

logger = logging.getLogger(__name__)

# Initialize use cases
verification_use_case = SendVerificationEmailUseCase()
password_reset_use_case = SendPasswordResetEmailUseCase()


async def send_email_task(ctx: dict[str, Any], email_data: dict[str, Any]) -> bool:
    """
    ARQ task to send emails based on email type.

    Args:
        ctx: ARQ context (contains redis pool and other info)
        email_data: Dictionary containing email task data

    Returns:
        True if email sent successfully, False otherwise
    """
    email_type = email_data.get("email_type")
    recipient = email_data.get("to", "unknown")

    try:
        if email_type == EmailType.VERIFICATION.value:
            # Validate with Pydantic schema
            try:
                task = VerificationEmailTask(**email_data)
            except Exception as validation_error:
                logger.error(f"Validation error for verification email task: {validation_error}", exc_info=True)
                raise

            logger.info(f"Sending verification email to {task.to}")

            # Create request and execute use case
            request = SendVerificationEmailRequest(
                to=str(task.to),
                verification_token=task.verification_token,
                user_name=task.user_name,
                user_email=task.user_email,
                expiry_hours=task.expiry_hours,
                company_name=task.company_name,
                logo_url=task.logo_url,
                custom_message=task.custom_message,
            )
            result = verification_use_case.execute(request)

        elif email_type == EmailType.PASSWORD_RESET.value:
            # Validate with Pydantic schema
            try:
                task = PasswordResetEmailTask(**email_data)
            except Exception as validation_error:
                logger.error(f"Validation error for password reset email task: {validation_error}", exc_info=True)
                raise

            logger.info(f"Sending password reset email to {task.to}")

            # Create request and execute use case
            request = SendPasswordResetEmailRequest(
                to=str(task.to),  # Convert EmailStr to str
                reset_token=task.reset_token,
                user_name=task.user_name,
                expiry_hours=task.expiry_hours,
                company_name=task.company_name,
            )
            result = password_reset_use_case.execute(request)

        elif email_type == EmailType.CUSTOM.value:
            # Validate with Pydantic schema
            try:
                task = CustomEmailTask(**email_data)
            except Exception as validation_error:
                logger.error(f"Validation error for custom email task: {validation_error}", exc_info=True)
                raise

            logger.info(f"Sending custom email to {task.to}: {task.subject}")

            # Use email_service directly for custom emails
            result = email_service.send_email(
                to=str(task.to),  # Convert EmailStr to str
                subject=task.subject,
                html_content=task.html_content,
                text_content=task.text_content,
            )

        else:
            error_msg = f"Unknown email type: {email_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if result:
            logger.info(f"✓ Email sent successfully: {email_type} to {recipient}")
        else:
            logger.error(f"✗ Failed to send email: {email_type} to {recipient} (check email service logs for details)")

        return result

    except ValueError as e:
        logger.error(f"Value error in send_email_task for {email_type} to {recipient}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in send_email_task for {email_type} to {recipient}: {type(e).__name__} - {str(e)}",
            exc_info=True,
        )
        raise


async def startup(ctx: dict[str, Any]) -> None:
    """
    Worker startup function - runs when worker starts.
    Initialize connections here if needed.
    """
    logger.info("ARQ Email worker starting up...")
    ctx["startup_complete"] = True


async def shutdown(ctx: dict[str, Any]) -> None:
    """
    Worker shutdown function - runs when worker stops.
    Clean up connections here if needed.
    """
    logger.info("ARQ Email worker shutting down...")


class WorkerSettings:
    """
    ARQ Worker settings configuration.
    """

    redis_settings = RedisSettings(
        host=env.REDIS_HOST,
        port=env.REDIS_PORT,
        database=env.REDIS_DB,
    )

    # Task functions available to the worker
    functions = [send_email_task]

    # Worker configuration
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = env.ARQ_MAX_JOBS
    job_timeout = env.ARQ_JOB_TIMEOUT
    queue_name = env.ARQ_QUEUE_NAME

    # Retry configuration
    max_tries = 3
    retry_delay = 60  # Retry after 60 seconds


async def enqueue_email(email_data: dict[str, Any]) -> str | None:
    """
    Enqueue an email task to be processed by the worker.

    Args:
        email_data: Dictionary containing email task data

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        redis = await get_redis_pool()
        job = await redis.enqueue_job("send_email_task", email_data)
        logger.info(f"Email job enqueued: {job.job_id}")
        await redis.close()
        return job.job_id
    except Exception as e:
        logger.error(f"Failed to enqueue email job: {e}", exc_info=True)
        return None
