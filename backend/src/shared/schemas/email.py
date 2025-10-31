from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class EmailType(str, Enum):
    """Types of emails that can be sent."""

    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    CUSTOM = "custom"


class EmailTask(BaseModel):
    """Base schema for email tasks."""

    email_type: EmailType
    to: EmailStr

    class Config:
        use_enum_values = True


class VerificationEmailTask(EmailTask):
    """Schema for use_cases email task."""

    email_type: EmailType = Field(default=EmailType.VERIFICATION, frozen=True)
    verification_token: str = Field(..., min_length=1)
    user_name: str | None = Field(default=None, description="User's display name")
    user_email: str | None = Field(default=None, description="User's email for display")
    expiry_hours: int | None = Field(default=24, description="Hours until use_cases link expires")
    company_name: str | None = Field(default=None, description="Company/App name")
    logo_url: str | None = Field(default=None, description="Company logo URL")
    custom_message: str | None = Field(default=None, description="Additional custom message")


class PasswordResetEmailTask(EmailTask):
    """Schema for password reset email task."""

    email_type: EmailType = Field(default=EmailType.PASSWORD_RESET, frozen=True)
    reset_token: str = Field(..., min_length=1)
    user_name: str | None = Field(default=None, description="User's display name")
    expiry_hours: int | None = Field(default=1, description="Hours until reset link expires")
    company_name: str | None = Field(default=None, description="Company/App name")


class CustomEmailTask(EmailTask):
    """Schema for custom email task."""

    email_type: EmailType = Field(default=EmailType.CUSTOM, frozen=True)
    subject: str = Field(..., min_length=1, max_length=200)
    html_content: str = Field(..., min_length=1)
    text_content: str | None = None
    context: dict[str, Any] | None = None
