"""Use case for sending password reset emails."""

import logging
from dataclasses import dataclass

from src.core.config.env import env
from src.modules.email.service import email_service


@dataclass
class SendPasswordResetEmailRequest:
    """Request data for sending password reset email."""

    to: str
    reset_token: str
    user_name: str | None = None
    expiry_hours: int = 1
    company_name: str | None = None


class SendPasswordResetEmailUseCase:
    """Use case for sending password reset emails to users."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute(self, request: SendPasswordResetEmailRequest) -> bool:
        """
        Send a password reset email to a user.

        Args:
            request: SendPasswordResetEmailRequest containing email details

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Build subject line
            subject = (
                f"Reset your password - {request.company_name}"
                if request.company_name
                else "Reset your password"
            )

            # Build template context
            context = {
                "reset_url": f"{env.FRONTEND_URL}/reset-password?token={request.reset_token}",
                "frontend_url": env.FRONTEND_URL,
                "support_email": env.EMAILS_FROM_EMAIL,
                "user_name": request.user_name or "there",
                "expiry_hours": request.expiry_hours,
                "company_name": request.company_name or env.EMAILS_FROM_NAME or "Our Team",
            }

            # Render email templates
            text_content, html_content = email_service.render_email("password_reset", context)

            # Send email
            result = email_service.send_email(
                to=request.to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

            if result:
                self.logger.info(f"Password reset email sent successfully to {request.to}")
            else:
                self.logger.error(f"Failed to send password reset email to {request.to}")

            return result

        except Exception as e:
            self.logger.error(f"Error sending password reset email to {request.to}: {e}", exc_info=True)
            return False

