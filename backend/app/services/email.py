"""
Email Service — OpenRAG
=======================

Handles all transactional email sending via SMTP (configurable for any provider:
SendGrid, AWS SES, Resend, Postmark, or self-hosted SMTP).

Configuration (add to Settings / .env):
    SMTP_HOST=smtp.sendgrid.net
    SMTP_PORT=587
    SMTP_USER=apikey
    SMTP_PASSWORD=your-sendgrid-api-key
    EMAIL_FROM_ADDRESS=noreply@openrag.com
    EMAIL_FROM_NAME=OpenRAG

Usage:
    from app.services.email import email_service

    await email_service.send_password_reset(
        to_email="user@example.com",
        reset_token="abc123",
        username="John"
    )
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger()


class EmailService:
    """
    Transactional email service using async-compatible SMTP.

    In development mode (ENVIRONMENT=development), all emails are logged
    to stdout instead of being sent — no SMTP server required.
    """

    def __init__(self) -> None:
        self.host: str = getattr(settings, "SMTP_HOST", "")
        self.port: int = getattr(settings, "SMTP_PORT", 587)
        self.user: str = getattr(settings, "SMTP_USER", "")
        self.password: str = getattr(settings, "SMTP_PASSWORD", "")
        self.from_address: str = getattr(
            settings, "EMAIL_FROM_ADDRESS", "noreply@openrag.com"
        )
        self.from_name: str = getattr(settings, "EMAIL_FROM_NAME", "OpenRAG")
        self._dev_mode: bool = settings.ENVIRONMENT == "development" or not self.host

    def _build_message(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_address}>"
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        return msg

    def _send(self, msg: MIMEMultipart, to_email: str) -> None:
        """Send via SMTP with STARTTLS. Runs in threadpool for async contexts."""
        context = ssl.create_default_context()
        with smtplib.SMTP(self.host, self.port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(self.user, self.password)
            server.sendmail(self.from_address, to_email, msg.as_string())

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> None:
        """
        Core send method. In dev mode, logs the email to console.
        In production, sends via SMTP in a thread pool executor.
        """
        if self._dev_mode:
            logger.info(
                "📧 [DEV] Email would be sent",
                to=to_email,
                subject=subject,
                preview=text_body[:120] if text_body else html_body[:120],
            )
            return

        import asyncio

        msg = self._build_message(to_email, subject, html_body, text_body)
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._send, msg, to_email)
            logger.info("Email sent successfully", to=to_email, subject=subject)
        except Exception as exc:
            logger.error(
                "Failed to send email", to=to_email, subject=subject, error=str(exc)
            )
            raise

    # ─── Public Email Templates ──────────────────────────────────────────────

    async def send_password_reset(
        self, to_email: str, reset_token: str, username: str = "there"
    ) -> None:
        """Send a password reset email with a secure tokenized link."""
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 40px;">
          <div style="max-width: 560px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h1 style="color: #0f172a; font-size: 24px; margin-bottom: 8px;">Reset your password</h1>
            <p style="color: #64748b; margin-bottom: 24px;">Hi {username}, we received a request to reset your OpenRAG password.</p>
            <a href="{reset_url}" style="display: inline-block; background: #0f172a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 500; margin-bottom: 24px;">
              Reset Password
            </a>
            <p style="color: #94a3b8; font-size: 14px;">This link expires in 15 minutes. If you didn't request this, you can safely ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px;">OpenRAG &mdash; Enterprise AI Platform &mdash; <a href="https://openrag.com" style="color: #94a3b8;">openrag.com</a></p>
          </div>
        </body>
        </html>
        """

        text_body = (
            f"Hi {username},\n\n"
            f"Reset your OpenRAG password by visiting:\n{reset_url}\n\n"
            f"This link expires in 15 minutes.\n\n"
            f"If you didn't request this, ignore this email.\n\n"
            f"— OpenRAG Team"
        )

        await self._send_email(
            to_email=to_email,
            subject="Reset your OpenRAG password",
            html_body=html_body,
            text_body=text_body,
        )

    async def send_welcome(self, to_email: str, username: str) -> None:
        """Send a welcome email to a newly registered user."""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 40px;">
          <div style="max-width: 560px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px;">
            <h1 style="color: #0f172a;">Welcome to OpenRAG, {username}! 👋</h1>
            <p style="color: #64748b;">Your enterprise AI workspace is ready. Everything stays within your infrastructure — zero telemetry, absolute privacy.</p>
            <a href="{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/chat" style="display: inline-block; background: #0f172a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 500; margin: 24px 0;">
              Open Workspace →
            </a>
            <p style="color: #94a3b8; font-size: 12px;">OpenRAG &mdash; Enterprise AI Platform</p>
          </div>
        </body>
        </html>
        """
        await self._send_email(
            to_email=to_email,
            subject="Welcome to OpenRAG",
            html_body=html_body,
        )

    async def send_mfa_enabled_notification(self, to_email: str, username: str) -> None:
        """Notify user that MFA has been enabled on their account."""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 40px;">
          <div style="max-width: 560px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px;">
            <h1 style="color: #0f172a;">🔐 Two-Factor Authentication Enabled</h1>
            <p style="color: #64748b;">Hi {username}, MFA has been successfully enabled on your OpenRAG account.</p>
            <p style="color: #64748b;">If you didn't make this change, please <a href="mailto:security@openrag.com" style="color: #0f172a;">contact security</a> immediately.</p>
            <p style="color: #94a3b8; font-size: 12px;">OpenRAG &mdash; Enterprise AI Platform</p>
          </div>
        </body>
        </html>
        """
        await self._send_email(
            to_email=to_email,
            subject="MFA enabled on your OpenRAG account",
            html_body=html_body,
        )


# Global singleton
email_service = EmailService()
