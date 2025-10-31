import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.core.config.env import env

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with template rendering support."""

    def __init__(self):
        """Initialize email service with template environment."""
        # Get template directory from settings or use default
        self.template_dir = Path(__file__).resolve().parents[3] / env.EMAIL_TEMPLATES_DIR

        self.template_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"])
        )
        self.email_template_prefix = "emails/"
        self.logger = logging.getLogger(self.__class__.__name__)

    def resolve_template_path(self, template_name: str) -> str:
        """
        Resolve full template path with prefix.

        Args:
            template_name: Name of the template (e.g., 'verification')

        Returns:
            Full template path (e.g., 'emails/verification')
        """
        path = Path(f"{self.email_template_prefix}{template_name}.html")
        # verify template exists
        if not (self.template_dir / path).exists():
            self.logger.warning(f"Template '{template_name}' not found in '{self.template_dir}'.")
            raise FileNotFoundError(f"Template '{template_name}' not found.")
        return f"{self.email_template_prefix}{template_name}"

    def render_email(self, template_base: str, context: dict) -> tuple[str, str]:
        """
        Render email templates (text and HTML).

        Args:
            template_base: Base path to template (e.g., 'verification')
            context: Template context variables

        Returns:
            Tuple of (text_content, html_content)
        """
        try:
            # Resolve the full template path with prefix
            full_template_path = self.resolve_template_path(template_base)

            html_tpl = self.template_env.get_template(f"{full_template_path}.html")
            txt_tpl = self.template_env.get_template(f"{full_template_path}.txt")

            html = html_tpl.render(**context)
            text = txt_tpl.render(**context)

            return text, html
        except Exception as e:
            self.logger.error(f"Error rendering email template '{template_base}': {e}")
            raise

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """
        Send an email using the configured SMTP settings.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            html_content: HTML content of the email
            text_content: Optional plain text content

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Validate SMTP configuration
        if not env.validate_smtp_config():
            missing_configs = []
            if not env.SMTP_HOST:
                missing_configs.append("SMTP_HOST")
            if not env.SMTP_PORT:
                missing_configs.append("SMTP_PORT")
            if not env.SMTP_USER:
                missing_configs.append("SMTP_USER")
            if not env.SMTP_PASSWORD:
                missing_configs.append("SMTP_PASSWORD")
            if not env.EMAILS_FROM_EMAIL:
                missing_configs.append("EMAILS_FROM_EMAIL")

            error_msg = f"Email not sent - SMTP not properly configured. Missing: {', '.join(missing_configs)}"
            self.logger.error(error_msg)
            return False

        # Convert to list if single recipient
        recipients = to if isinstance(to, list) else [to]

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{env.EMAILS_FROM_NAME or 'App'} <{env.EMAILS_FROM_EMAIL}>"
            message["To"] = ", ".join(recipients)

            # Add plain text part
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            self.logger.info(
                f"Attempting to send email to {recipients} via {env.SMTP_HOST}:{env.SMTP_PORT} (TLS={env.SMTP_TLS})"
            )

            # Connect and send email
            if env.SMTP_PORT == 465:
                # Use SSL for port 465
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(env.SMTP_HOST, env.SMTP_PORT, context=context, timeout=30) as server:
                    server.login(env.SMTP_USER, env.SMTP_PASSWORD)
                    server.sendmail(env.EMAILS_FROM_EMAIL, recipients, message.as_string())
            else:
                # Use STARTTLS for port 587
                with smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT, timeout=30) as server:
                    server.set_debuglevel(0)  # Set to 1 for debug output
                    if env.SMTP_TLS:
                        server.starttls(context=ssl.create_default_context())
                    server.login(env.SMTP_USER, env.SMTP_PASSWORD)
                    server.sendmail(env.EMAILS_FROM_EMAIL, recipients, message.as_string())

            success_msg = f"✓ Email sent successfully: '{subject}' to {recipients}"
            self.logger.info(success_msg)
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"✗ SMTP Authentication failed for {recipients}: {e.smtp_code} - {e.smtp_error.decode() if e.smtp_error else 'Unknown error'}"
            self.logger.error(error_msg, exc_info=True)
            return False
        except smtplib.SMTPConnectError as e:
            error_msg = f"✗ Cannot connect to SMTP server {env.SMTP_HOST}:{env.SMTP_PORT}: {e.smtp_code} - {e.smtp_error.decode() if e.smtp_error else 'Unknown error'}"
            self.logger.error(error_msg, exc_info=True)
            return False
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"✗ SMTP server disconnected unexpectedly when sending to {recipients}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False
        except smtplib.SMTPException as e:
            error_msg = f"✗ SMTP error sending email to {recipients}: {type(e).__name__} - {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False
        except ConnectionRefusedError as e:
            error_msg = f"✗ Connection refused when sending email to {recipients}: Cannot connect to SMTP server {env.SMTP_HOST}:{env.SMTP_PORT}. Error: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False
        except TimeoutError as e:
            error_msg = (
                f"✗ Timeout error sending email to {recipients}: SMTP server did not respond in time. Error: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            return False
        except Exception as e:
            error_msg = f"✗ Unexpected error sending email to {recipients}: {type(e).__name__} - {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False


# Create a singleton instance
email_service = EmailService()

