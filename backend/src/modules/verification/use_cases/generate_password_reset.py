"""
Use case: Generate and send password reset code.
"""

from src.core.verification import VerificationOptions, VerificationService
from src.workers.helpers import queue_password_reset_email


class GeneratePasswordResetUseCase:
    """
    Use case for generating and sending password reset code.

    Responsibilities:
    - Generate password reset code with stricter security settings
    - Queue email to be sent by worker
    - Handle rate limiting (stricter than email use_cases)
    """

    def __init__(self, verification_service: VerificationService):
        """
        Initialize use case.

        Args:
            verification_service: VerificationService instance
        """
        self.verification_service = verification_service

    async def execute(self, email: str, ttl_sec: int = 1800) -> str:
        """
        Execute the use case.

        Args:
            email: User's email address
            ttl_sec: Time to live in seconds (default 30 minutes)

        Returns:
            Job ID from email queue

        Raises:
            Exception: If rate limit exceeded or validation fails
        """
        # Generate reset code with stricter settings
        result = await self.verification_service.generate(
            VerificationOptions(
                namespace="password-reset",
                subject=email,
                ttl_sec=ttl_sec,
                max_attempts=3,  # Fewer attempts for security
                length=8,  # Longer code for password reset
                rate_limit_window_sec=300,  # 5 minutes
                rate_limit_max=2,  # Only 2 requests per 5 minutes
            )
        )

        # Queue email to be sent by worker
        job_id = await queue_password_reset_email(email=email, reset_token=result.code)

        return job_id
