"""
Helper class for use_cases use cases.
Provides convenient wrappers around use cases with dependency injection support.
"""

from fastapi import Depends

from src.core.verification import VerificationService, get_verification_service

from .generate_email_verification import GenerateEmailVerificationUseCase
from .generate_password_reset import GeneratePasswordResetUseCase
from .verify_email_code import VerifyEmailCodeUseCase
from .verify_password_reset_code import VerifyPasswordResetCodeUseCase


class VerificationUseCase:
    """
    Helper class that wraps use_cases use cases.
    Designed to be used with FastAPI dependency injection.

    Example:
        @app.post("/auth/register")
        async def register(
            helper: VerificationHelper = Depends(get_verification_helper)
        ):
            job_id = await helper.send_email_verification(
                email="user@example.com",
                user_name="John Doe",
                company_name="My App"
            )
    """

    def __init__(self, verification_service: VerificationService):
        """
        Initialize helper with use_cases service.

        Args:
            verification_service: VerificationService instance
        """
        self.verification_service = verification_service
        self._email_verification_use_case = GenerateEmailVerificationUseCase(verification_service)
        self._verify_email_use_case = VerifyEmailCodeUseCase(verification_service)
        self._password_reset_use_case = GeneratePasswordResetUseCase(verification_service)
        self._verify_reset_use_case = VerifyPasswordResetCodeUseCase(verification_service)

    async def send_email_verification(
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
        Generate and send email use_cases code.

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
            Exception: If rate limit exceeded
        """
        return await self._email_verification_use_case.execute(
            email=email,
            ttl_sec=ttl_sec,
            user_name=user_name,
            user_email=user_email,
            expiry_hours=expiry_hours,
            company_name=company_name,
            logo_url=logo_url,
            custom_message=custom_message,
        )

    async def verify_email(self, email: str, code: str) -> dict:
        """
        Verify email use_cases code.

        Args:
            email: User's email address
            code: Verification code

        Returns:
            Dictionary with use_cases result and remaining attempts
            {
                "valid": bool,
                "remaining_attempts": int | None
            }
        """
        return await self._verify_email_use_case.execute(email, code)

    async def send_password_reset(self, email: str, ttl_sec: int = 1800) -> str:
        """
        Generate and send password reset code.

        Args:
            email: User's email address
            ttl_sec: Time to live in seconds (default 30 minutes)

        Returns:
            Job ID from email queue

        Raises:
            Exception: If rate limit exceeded
        """
        return await self._password_reset_use_case.execute(email, ttl_sec)

    async def verify_password_reset(self, email: str, code: str) -> dict:
        """
        Verify password reset code.

        Args:
            email: User's email address
            code: Reset code

        Returns:
            Dictionary with use_cases result and remaining attempts
            {
                "valid": bool,
                "remaining_attempts": int | None
            }
        """
        return await self._verify_reset_use_case.execute(email, code)


# FastAPI Dependency
async def get_verification_usecase(
    verification_service: VerificationService = Depends(get_verification_service),
) -> VerificationUseCase:
    """
    FastAPI dependency to get VerificationHelper instance.

    Returns:
        VerificationHelper instance
    """
    return VerificationUseCase(verification_service)
