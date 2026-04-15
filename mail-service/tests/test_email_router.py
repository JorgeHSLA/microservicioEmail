from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_email_service
from app.core.exceptions import EmailSendError
from app.main import app
from app.schemas.email_schemas import EmailResponse
from app.services.email_service import EmailService


class TestEmailRouter:
    """Integration tests for email endpoint using TestClient."""

    @pytest.fixture
    def mock_email_service(self) -> MagicMock:
        return MagicMock(spec=EmailService)

    @pytest.fixture
    def client(self, mock_email_service: MagicMock) -> TestClient:
        app.dependency_overrides[get_email_service] = lambda: mock_email_service
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def valid_payload(self) -> dict:
        return {
            "to_emails": ["dest@example.com"],
            "subject": "Confirmación de reserva",
            "body": "Tu paquete turístico ha sido confirmado.",
        }

    def test_send_email_returns_200(
        self,
        client: TestClient,
        mock_email_service: MagicMock,
        valid_payload: dict,
    ) -> None:
        mock_email_service.send_email.return_value = EmailResponse(
            status="sent",
            recipients=["dest@example.com"],
        )

        response = client.post("/api/v1/emails", json=valid_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["recipients"] == ["dest@example.com"]

    def test_send_email_returns_502_on_smtp_error(
        self,
        client: TestClient,
        mock_email_service: MagicMock,
        valid_payload: dict,
    ) -> None:
        mock_email_service.send_email.side_effect = EmailSendError(
            "SMTP connection failed"
        )

        response = client.post("/api/v1/emails", json=valid_payload)

        assert response.status_code == 502
        assert "SMTP connection failed" in response.json()["detail"]

    def test_send_email_returns_422_on_missing_subject(
        self, client: TestClient
    ) -> None:
        payload = {
            "to_emails": ["dest@example.com"],
            "body": "Some body",
        }

        response = client.post("/api/v1/emails", json=payload)

        assert response.status_code == 422

    def test_send_email_returns_422_on_invalid_email(
        self, client: TestClient
    ) -> None:
        payload = {
            "to_emails": ["not-an-email"],
            "subject": "Test",
            "body": "Some body",
        }

        response = client.post("/api/v1/emails", json=payload)

        assert response.status_code == 422

    def test_send_email_returns_422_on_empty_body(
        self, client: TestClient
    ) -> None:
        payload = {
            "to_emails": ["dest@example.com"],
            "subject": "Test",
            "body": "",
        }

        response = client.post("/api/v1/emails", json=payload)

        assert response.status_code == 422

    def test_send_email_returns_422_on_empty_recipients(
        self, client: TestClient
    ) -> None:
        payload = {
            "to_emails": [],
            "subject": "Test",
            "body": "Some body",
        }

        response = client.post("/api/v1/emails", json=payload)

        assert response.status_code == 422


class TestHealthRouter:
    """Integration tests for health endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
