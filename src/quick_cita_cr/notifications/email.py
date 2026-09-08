from __future__ import annotations

import smtplib
from email.message import EmailMessage

from pydantic import SecretStr

from quick_cita_cr.config import EmailConfig


class EmailNotifier:
    def __init__(self, config: EmailConfig, username: str, password: SecretStr):
        if not config.from_address:
            raise ValueError("email from_address is required")
        if not config.to_addresses:
            raise ValueError("at least one email recipient is required")
        self.config = config
        self.username = username
        self.password = password

    def send(self, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.config.from_address
        message["To"] = ", ".join(self.config.to_addresses)
        message.set_content(body)

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.username, self.password.get_secret_value())
            smtp.send_message(message)
