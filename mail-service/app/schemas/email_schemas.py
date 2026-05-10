from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    """Email payload. Wire JSON uses camelCase (`toEmails`) for consistency with
    the rest of the platform. Snake_case `to_emails` is also accepted thanks to
    `populate_by_name=True` so existing Spring clients keep working unchanged.
    """

    to_emails: list[EmailStr] = Field(min_length=1, alias="toEmails")
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)

    model_config = {"populate_by_name": True}


class EmailResponse(BaseModel):
    status: Literal["sent"]
    recipients: list[EmailStr]
