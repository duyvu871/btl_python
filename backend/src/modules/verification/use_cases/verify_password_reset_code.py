"""
Use case: Verify password reset code.
"""

from src.core.verification import VerificationOptions, VerificationService


class VerifyPasswordResetCodeUseCase:
    """
    Use case for verifying password reset code.

    Responsibilities:
    - Verify the reset code against stored hash
    - Consume the code (one-time use)
    - Track remaining attempts
    """

    def __init__(self, verification_service: VerificationService):
        """
        Initialize use case.

        Args:
            verification_service: VerificationService instance
        """
        self.verification_service = verification_service

    async def execute(self, email: str, code: str) -> dict:
        """
        Execute the use case.

        Args:
            email: User's email address
            code: Reset code to verify

        Returns:
            Dictionary with use_cases result and remaining attempts
            {
                "valid": bool,
                "remaining_attempts": int | None
            }
        """
        # Verify and consume code
        valid = await self.verification_service.verify_and_consume(
            VerificationOptions(namespace="password-reset", subject=email), code=code
        )

        # Get remaining attempts if use_cases failed
        remaining_attempts = None
        if not valid:
            remaining_attempts = await self.verification_service.get_remaining_attempts(
                namespace="password-reset", subject=email
            )

        return {"valid": valid, "remaining_attempts": remaining_attempts}
