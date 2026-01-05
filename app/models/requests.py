"""Pydantic models for API requests."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RequestCodeRequest(BaseModel):
    """Request model for requesting verification code."""
    phone: str = Field(..., description="Phone number in international format (+1234567890)", min_length=10)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove spaces and dashes
        phone = v.replace(' ', '').replace('-', '')

        # Must start with +
        if not phone.startswith('+'):
            raise ValueError('Phone number must start with + (international format)')

        # Must contain only digits after +
        if not phone[1:].isdigit():
            raise ValueError('Phone number must contain only digits after +')

        return phone


class VerifyCodeRequest(BaseModel):
    """Request model for verifying phone code."""
    phone: str = Field(..., description="Phone number in international format")
    code: str = Field(..., description="Verification code from Telegram", min_length=5, max_length=6)
    phone_code_hash: str = Field(..., description="Hash received from request-code endpoint")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        phone = v.replace(' ', '').replace('-', '')
        if not phone.startswith('+'):
            raise ValueError('Phone number must start with + (international format)')
        if not phone[1:].isdigit():
            raise ValueError('Phone number must contain only digits after +')
        return phone

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate verification code."""
        # Remove spaces
        code = v.replace(' ', '')

        # Must be digits only
        if not code.isdigit():
            raise ValueError('Verification code must contain only digits')

        return code


class Verify2FARequest(BaseModel):
    """Request model for 2FA password verification."""
    phone: str = Field(..., description="Phone number in international format")
    password: str = Field(..., description="Two-factor authentication password", min_length=1)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        phone = v.replace(' ', '').replace('-', '')
        if not phone.startswith('+'):
            raise ValueError('Phone number must start with + (international format)')
        if not phone[1:].isdigit():
            raise ValueError('Phone number must contain only digits after +')
        return phone


class GetMessagesQuery(BaseModel):
    """Query parameters for getting messages from a channel."""
    limit: int = Field(
        default=20,
        description="Number of messages to retrieve",
        ge=1,
        le=100
    )
    offset_id: int = Field(
        default=0,
        description="Message ID to use as offset for pagination",
        ge=0
    )
    date_from: Optional[datetime] = Field(
        None,
        description="Start date for filtering messages (ISO 8601 format)"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="End date for filtering messages (ISO 8601 format)"
    )
    include_media: bool = Field(
        default=True,
        description="Whether to include media information"
    )
    media_format: str = Field(
        default="url",
        description="Media format: 'url' or 'base64'",
        pattern="^(url|base64)$"
    )

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate limit is within acceptable range."""
        from config import settings
        if v > settings.max_messages_per_request:
            raise ValueError(
                f'Limit cannot exceed {settings.max_messages_per_request}'
            )
        return v
