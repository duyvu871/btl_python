"""
Use case: Generate and send email use_cases code.
"""

from src.core.verification import VerificationOptions, VerificationService
from src.workers.helpers import queue_verification_email


class GenerateEmailVerificationUseCase:
    """
    Use case for generating and sending email use_cases code.

    Responsibilities:
    - Generate use_cases code with proper configuration
    - Queue email to be sent by worker
    - Handle rate limiting
    """

    def __init__(self, verification_service: VerificationService):
        """
        Initialize use case.

        Args:
            verification_service: VerificationService instance
        """
        self.verification_service = verification_service

    async def execute(
        self,
        email: str,
        ttl_sec: int = 600,
        user_name: str | None = None,
        user_email: str | None = None,
        expiry_hours: int = 24,
        company_name: str | None = None,
        logo_url: str | None = None,
        custom_message: str | None = None,
    ) -> str:
        """
        Execute the use case.

        Args:
            email: User's email address
            ttl_sec: Time to live in seconds (default 10 minutes)
            user_name: User's display name (optional)
            user_email: User's email for display (optional)
            expiry_hours: Hours until use_cases link expires (default: 24)
            company_name: Company/App name (optional)
            logo_url: Company logo URL (optional)
            custom_message: Additional custom message (optional)

        Returns:
            Job ID from email queue

        Raises:
            Exception: If rate limit exceeded or validation fails
        """
        # Generate use_cases code
        result = await self.verification_service.generate(
            VerificationOptions(
                namespace="email-verify",
                subject=email,
                ttl_sec=ttl_sec,
                max_attempts=5,
                length=6,
                rate_limit_window_sec=60,
                rate_limit_max=3,
            )
        )

        # Queue email to be sent by worker with all parameters
        job_id = await queue_verification_email(
            email=email,
            verification_token=result.code,
            user_name=user_name,
            user_email=user_email,
            expiry_hours=expiry_hours,
            company_name=company_name,
            logo_url=logo_url,
            custom_message=custom_message,
        )

        return job_id
