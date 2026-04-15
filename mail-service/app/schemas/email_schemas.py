from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    to_emails: list[EmailStr] = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class EmailResponse(BaseModel):
    status: Literal["sent"]
    recipients: list[EmailStr]
