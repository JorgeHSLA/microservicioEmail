import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.exceptions import EmailSendError


class GmailSmtpClient:
    def __init__(self, host: str, port: int, user: str, password: str, from_name: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from_name = from_name

    def send(self, to_emails: list[str], subject: str, body: str, is_html: bool = True) -> None:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self._from_name} <{self._user}>"
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))

        server: smtplib.SMTP | None = None
        try:
            server = smtplib.SMTP(self._host, self._port)
            server.starttls()
            server.login(self._user, self._password)
            server.send_message(msg)
        except (smtplib.SMTPException, OSError) as exc:
            raise EmailSendError(
                message=f"Failed to send email: {exc}",
                original_error=exc,
            ) from exc
        finally:
            if server is not None:
                server.quit()
