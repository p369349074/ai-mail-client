from dataclasses import dataclass
import imaplib
import smtplib
import socket

from app.core.config import settings
from app.models.mail import MailSecurityMode


@dataclass(frozen=True)
class MailServerConfig:
    host: str
    port: int
    security: MailSecurityMode


@dataclass(frozen=True)
class MailAccountConnectionConfig:
    email: str
    imap: MailServerConfig
    smtp: MailServerConfig


@dataclass(frozen=True)
class MailConnectivityResult:
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class MailConnectivityReport:
    imap: MailConnectivityResult
    smtp: MailConnectivityResult


class MailConnectivityService:
    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.timeout_seconds = timeout_seconds or settings.mail_connect_timeout_seconds

    def test_account(self, config: MailAccountConnectionConfig, password: str) -> MailConnectivityReport:
        return MailConnectivityReport(
            imap=self.test_imap(config.email, password, config.imap),
            smtp=self.test_smtp(config.email, password, config.smtp),
        )

    def test_imap(self, username: str, password: str, server: MailServerConfig) -> MailConnectivityResult:
        client: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None
        try:
            if server.security == MailSecurityMode.ssl:
                client = imaplib.IMAP4_SSL(server.host, server.port, timeout=self.timeout_seconds)
            else:
                client = imaplib.IMAP4(server.host, server.port, timeout=self.timeout_seconds)
                if server.security == MailSecurityMode.starttls:
                    client.starttls()
            client.login(username, password)
            return MailConnectivityResult(ok=True)
        except Exception as exc:
            return MailConnectivityResult(ok=False, error=self._safe_error_message(exc))
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass

    def test_smtp(self, username: str, password: str, server: MailServerConfig) -> MailConnectivityResult:
        client: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        try:
            if server.security == MailSecurityMode.ssl:
                client = smtplib.SMTP_SSL(server.host, server.port, timeout=self.timeout_seconds)
            else:
                client = smtplib.SMTP(server.host, server.port, timeout=self.timeout_seconds)
                client.ehlo()
                if server.security == MailSecurityMode.starttls:
                    client.starttls()
                    client.ehlo()
            client.login(username, password)
            return MailConnectivityResult(ok=True)
        except Exception as exc:
            return MailConnectivityResult(ok=False, error=self._safe_error_message(exc))
        finally:
            if client is not None:
                try:
                    client.quit()
                except Exception:
                    pass

    def _safe_error_message(self, exc: Exception) -> str:
        if isinstance(exc, (TimeoutError, socket.timeout)):
            return "Connection timed out."
        if isinstance(exc, (imaplib.IMAP4.error, smtplib.SMTPAuthenticationError)):
            return "Authentication failed or was rejected by the mail server."
        if isinstance(exc, (OSError, smtplib.SMTPException)):
            return "Could not connect to the mail server with the provided settings."
        return "Mail connectivity check failed."


def get_mail_connectivity_service() -> MailConnectivityService:
    return MailConnectivityService()
