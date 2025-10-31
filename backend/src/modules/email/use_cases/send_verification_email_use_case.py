"""Use case for sending verification emails."""

import logging
from dataclasses import dataclass

from src.core.config.env import env
from src.modules.email.service import email_service


@dataclass
class SendVerificationEmailRequest:
    """Request data for sending verification email."""

    to: str
    verification_token: str
    user_name: str | None = None
    user_email: str | None = None
    expiry_hours: int = 24
    company_name: str | None = None
    logo_url: str | None = None
    custom_message: str | None = None


class SendVerificationEmailUseCase:
    """Use case for sending verification emails to users."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute(self, request: SendVerificationEmailRequest) -> bool:
        """
        Send a verification email to a user.

        Args:
            request: SendVerificationEmailRequest containing email details

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Build subject line
            subject = (
                f"Verify your email - {request.company_name}"
                if request.company_name
                else "Verify your email"
            )

            # Build template context
            context = {
                "verification_code": request.verification_token,
                "verification_url": f"{env.FRONTEND_URL}/verify-email?email={request.to}&code={request.verification_token}",
                "frontend_url": env.FRONTEND_URL,
                "support_email": env.EMAILS_FROM_EMAIL,
                "user_name": request.user_name or "there",
                "user_email": request.user_email or request.to,
                "expiry_hours": request.expiry_hours,
                "company_name": request.company_name or env.EMAILS_FROM_NAME or "Our Team",
                "logo_url": request.logo_url,
                "custom_message": request.custom_message,
            }

            # Render email templates
            text_content, html_content = email_service.render_email("verification", context)

            # Send email
            result = email_service.send_email(
                to=request.to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

            if result:
                self.logger.info(f"Verification email sent successfully to {request.to}")
            else:
                self.logger.error(f"Failed to send verification email to {request.to}")

            return result

        except Exception as e:
            self.logger.error(f"Error sending verification email to {request.to}: {e}", exc_info=True)
            return False

