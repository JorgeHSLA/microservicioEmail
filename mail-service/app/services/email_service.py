from app.infrastructure.smtp.gmail_smtp_client import GmailSmtpClient
from app.infrastructure.templates.template_renderer import EmailTemplateRenderer
from app.schemas.email_schemas import EmailRequest, EmailResponse


class EmailService:
    def __init__(self, smtp_client: GmailSmtpClient, template_renderer: EmailTemplateRenderer) -> None:
        self._smtp_client = smtp_client
        self._template_renderer = template_renderer

    def send_email(self, request: EmailRequest) -> EmailResponse:
        html_body = self._template_renderer.render(
            "generic_message.html",
            {
                "subject": request.subject,
                "body": request.body,
                "platform_name": "Turismo Platform",
            },
        )

        self._smtp_client.send(
            to_emails=[str(email) for email in request.to_emails],
            subject=request.subject,
            body=html_body,
            is_html=True,
        )

        return EmailResponse(status="sent", recipients=request.to_emails)
