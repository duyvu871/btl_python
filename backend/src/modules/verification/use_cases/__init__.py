"""
Verification use cases.

This package contains all use cases related to use_cases workflows:
- Email use_cases
- Password reset
- 2FA (future)
"""

from .generate_email_verification import GenerateEmailVerificationUseCase
from .generate_password_reset import GeneratePasswordResetUseCase
from .helpers import (
    VerificationUseCase,
    get_verification_usecase,
)
from .verify_email_code import VerifyEmailCodeUseCase
from .verify_password_reset_code import VerifyPasswordResetCodeUseCase

__all__ = [
    # Use cases
    "GenerateEmailVerificationUseCase",
    "VerifyEmailCodeUseCase",
    "GeneratePasswordResetUseCase",
    "VerifyPasswordResetCodeUseCase",
    # Helpers
    "VerificationUseCase",
    "get_verification_usecase",
]
