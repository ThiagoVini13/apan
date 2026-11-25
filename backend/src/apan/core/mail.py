"""Outgoing e-mail.

Messages are sent in the background so a request never waits for (or leaks
timing about) the SMTP server.
"""

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import structlog

from apan.core.config import Settings

_logger = structlog.get_logger("apan.mail")


@dataclass(frozen=True, slots=True)
class Mail:
    to: str
    subject: str
    body: str


class Mailer(Protocol):
    def send(self, mail: Mail) -> None: ...


class SmtpMailer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._tasks: set[asyncio.Task[None]] = set()

    def send(self, mail: Mail) -> None:
        task = asyncio.get_running_loop().create_task(self._deliver(mail))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _deliver(self, mail: Mail) -> None:
        try:
            await asyncio.to_thread(self._send_sync, mail)
        except Exception as exc:
            _logger.error("mail_delivery_failed", subject=mail.subject, error=type(exc).__name__)

    def _send_sync(self, mail: Mail) -> None:
        message = EmailMessage()
        message["From"] = self._settings.mail_from
        message["To"] = mail.to
        message["Subject"] = mail.subject
        message.set_content(mail.body)

        settings = self._settings
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)

    async def drain(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
