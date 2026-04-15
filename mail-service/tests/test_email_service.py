from unittest.mock import MagicMock

import pytest

from app.core.exceptions import EmailSendError
from app.infrastructure.smtp.gmail_smtp_client import GmailSmtpClient
from app.infrastructure.templates.template_renderer import EmailTemplateRenderer
from app.schemas.email_schemas import EmailRequest
from app.services.email_service import EmailService


class TestEmailService:
    """Unit tests for EmailService with mocked dependencies."""

    @pytest.fixture
    def mock_smtp_client(self) -> MagicMock:
        return MagicMock(spec=GmailSmtpClient)

    @pytest.fixture
    def mock_template_renderer(self) -> MagicMock:
        return MagicMock(spec=EmailTemplateRenderer)

    @pytest.fixture
    def email_service(
        self, mock_smtp_client: MagicMock, mock_template_renderer: MagicMock
    ) -> EmailService:
        return EmailService(
            smtp_client=mock_smtp_client,
            template_renderer=mock_template_renderer,
        )

    @pytest.fixture
    def sample_request(self) -> EmailRequest:
        return EmailRequest(
            to_emails=["dest@example.com"],
            subject="Test Subject",
            body="Test body content",
        )

    def test_send_email_calls_renderer_with_correct_args(
        self,
        email_service: EmailService,
        mock_template_renderer: MagicMock,
        sample_request: EmailRequest,
    ) -> None:
        mock_template_renderer.render.return_value = "<html>rendered</html>"

        email_service.send_email(sample_request)

        mock_template_renderer.render.assert_called_once_with(
            "generic_message.html",
            {
                "subject": "Test Subject",
                "body": "Test body content",
                "platform_name": "Turismo Platform",
            },
        )

    def test_send_email_calls_smtp_with_rendered_html(
        self,
        email_service: EmailService,
        mock_smtp_client: MagicMock,
        mock_template_renderer: MagicMock,
        sample_request: EmailRequest,
    ) -> None:
        mock_template_renderer.render.return_value = "<html>rendered</html>"

        email_service.send_email(sample_request)

        mock_smtp_client.send.assert_called_once_with(
            to_emails=["dest@example.com"],
            subject="Test Subject",
            body="<html>rendered</html>",
            is_html=True,
        )

    def test_send_email_returns_correct_response(
        self,
        email_service: EmailService,
        mock_template_renderer: MagicMock,
        sample_request: EmailRequest,
    ) -> None:
        mock_template_renderer.render.return_value = "<html>rendered</html>"

        response = email_service.send_email(sample_request)

        assert response.status == "sent"
        assert response.recipients == ["dest@example.com"]

    def test_send_email_propagates_smtp_error(
        self,
        email_service: EmailService,
        mock_smtp_client: MagicMock,
        mock_template_renderer: MagicMock,
        sample_request: EmailRequest,
    ) -> None:
        mock_template_renderer.render.return_value = "<html>rendered</html>"
        mock_smtp_client.send.side_effect = EmailSendError("SMTP connection failed")

        with pytest.raises(EmailSendError, match="SMTP connection failed"):
            email_service.send_email(sample_request)

    def test_send_email_propagates_template_error(
        self,
        email_service: EmailService,
        mock_template_renderer: MagicMock,
        sample_request: EmailRequest,
    ) -> None:
        mock_template_renderer.render.side_effect = EmailSendError("Template not found: generic_message.html")

        with pytest.raises(EmailSendError, match="Template not found"):
            email_service.send_email(sample_request)

    def test_send_email_with_multiple_recipients(
        self,
        email_service: EmailService,
        mock_smtp_client: MagicMock,
        mock_template_renderer: MagicMock,
    ) -> None:
        mock_template_renderer.render.return_value = "<html>multi</html>"
        request = EmailRequest(
            to_emails=["a@example.com", "b@example.com"],
            subject="Multi",
            body="To many",
        )

        response = email_service.send_email(request)

        assert response.recipients == ["a@example.com", "b@example.com"]
        mock_smtp_client.send.assert_called_once_with(
            to_emails=["a@example.com", "b@example.com"],
            subject="Multi",
            body="<html>multi</html>",
            is_html=True,
        )
