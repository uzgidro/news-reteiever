"""Pydantic models for API responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ReactionInfo(BaseModel):
    """Information about a message reaction."""
    emoji: str = Field(..., description="Reaction emoji")
    count: int = Field(..., description="Number of reactions")


class AuthorInfo(BaseModel):
    """Information about message author."""
    id: Optional[int] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")


class MediaInfo(BaseModel):
    """Information about media file in a message."""
    type: str = Field(..., description="Media type (photo, video, document, etc.)")
    url: Optional[str] = Field(None, description="URL to download the media")
    thumbnail_url: Optional[str] = Field(None, description="URL to thumbnail")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    duration: Optional[int] = Field(None, description="Duration in seconds (for videos/audio)")
    width: Optional[int] = Field(None, description="Width in pixels (for photos/videos)")
    height: Optional[int] = Field(None, description="Height in pixels (for photos/videos)")
    file_name: Optional[str] = Field(None, description="Original file name")


class MessageResponse(BaseModel):
    """Response model for a single message."""
    id: int = Field(..., description="Message ID")
    text: Optional[str] = Field(None, description="Message text content")
    date: datetime = Field(..., description="Message date and time")
    views: Optional[int] = Field(None, description="Number of views")
    forwards: Optional[int] = Field(None, description="Number of forwards")
    reactions: Optional[List[ReactionInfo]] = Field(None, description="Message reactions")
    author: Optional[AuthorInfo] = Field(None, description="Message author info")
    media: Optional[MediaInfo] = Field(None, description="Media file information")
    reply_to_message_id: Optional[int] = Field(None, description="ID of message being replied to")
    edit_date: Optional[datetime] = Field(None, description="Last edit date and time")
    has_protected_content: bool = Field(False, description="Whether content is protected")


class PaginationInfo(BaseModel):
    """Pagination information for message list."""
    total_fetched: int = Field(..., description="Number of messages in current response")
    next_offset_id: Optional[int] = Field(None, description="Offset ID for next page")
    has_more: bool = Field(..., description="Whether more messages are available")


class MessagesResponse(BaseModel):
    """Response model for messages list."""
    channel_id: int = Field(..., description="Channel ID")
    channel_title: str = Field(..., description="Channel title")
    messages: List[MessageResponse] = Field(..., description="List of messages")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class ChannelInfo(BaseModel):
    """Information about a Telegram channel."""
    id: int = Field(..., description="Channel ID")
    username: Optional[str] = Field(None, description="Channel username")
    title: str = Field(..., description="Channel title")
    description: Optional[str] = Field(None, description="Channel description")
    participants_count: Optional[int] = Field(None, description="Number of participants")
    photo_url: Optional[str] = Field(None, description="Channel photo URL")


class ChannelsListResponse(BaseModel):
    """Response model for channels list."""
    channels: List[ChannelInfo] = Field(..., description="List of channels")


class AuthStatusResponse(BaseModel):
    """Response model for authentication status."""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user_id: Optional[int] = Field(None, description="User ID if authenticated")
    username: Optional[str] = Field(None, description="Username if authenticated")
    phone: Optional[str] = Field(None, description="Phone number if authenticated")


class CodeSentResponse(BaseModel):
    """Response after sending verification code."""
    phone_code_hash: str = Field(..., description="Hash to use for code verification")
    message: str = Field(..., description="Informational message")


class AuthSuccessResponse(BaseModel):
    """Response after successful authentication."""
    success: bool = Field(True, description="Authentication success status")
    user_id: int = Field(..., description="Authenticated user ID")
    session_active: bool = Field(True, description="Whether session is active")
    message: str = Field("Authentication successful", description="Success message")


class TwoFactorRequiredResponse(BaseModel):
    """Response when 2FA is required."""
    success: bool = Field(False, description="Authentication not complete")
    two_factor_required: bool = Field(True, description="2FA required flag")
    message: str = Field("Two-factor authentication required", description="Info message")


class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""
    status: str = Field(..., description="Service status")
    telegram_connected: bool = Field(..., description="Whether Telegram client is connected")
    telegram_authenticated: bool = Field(..., description="Whether authenticated with Telegram")
