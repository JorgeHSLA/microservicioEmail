from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_email_service
from app.core.exceptions import EmailSendError
from app.schemas.email_schemas import EmailRequest, EmailResponse
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


@router.post("", response_model=EmailResponse)
def send_email(
    request: EmailRequest,
    service: EmailService = Depends(get_email_service),
) -> EmailResponse:
    try:
        return service.send_email(request)
    except EmailSendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
