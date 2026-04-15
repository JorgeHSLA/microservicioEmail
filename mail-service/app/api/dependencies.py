from fastapi import Depends

from app.core.config import Settings, get_settings
from app.infrastructure.smtp.gmail_smtp_client import GmailSmtpClient
from app.infrastructure.templates.template_renderer import EmailTemplateRenderer
from app.services.email_service import EmailService


def get_smtp_client(settings: Settings = Depends(get_settings)) -> GmailSmtpClient:
    return GmailSmtpClient(
        host=settings.gmail_host,
        port=settings.gmail_port,
        user=settings.gmail_user,
        password=settings.gmail_password.get_secret_value(),
        from_name=settings.from_name,
    )


def get_template_renderer(settings: Settings = Depends(get_settings)) -> EmailTemplateRenderer:
    return EmailTemplateRenderer(templates_dir=settings.templates_dir)


def get_email_service(
    smtp_client: GmailSmtpClient = Depends(get_smtp_client),
    template_renderer: EmailTemplateRenderer = Depends(get_template_renderer),
) -> EmailService:
    return EmailService(smtp_client=smtp_client, template_renderer=template_renderer)
