"""Messages API routes for microservice."""

import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Query, Request

from app.core.telegram_client import telegram_manager
from app.core.exceptions import (
    TelegramNotAuthenticatedError,
    ChannelNotFoundError,
    MessageNotFoundError
)
from app.services.message_service import MessageService
from app.services.media_service import MediaService
from app.models.responses import MessagesResponse, PaginationInfo
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=MessagesResponse,
    summary="Get messages from configured channel",
    description="Fetch messages from the configured Telegram channel (microservice endpoint)"
)
async def get_messages(
    request: Request,
    limit: Annotated[int, Query(
        ge=1,
        le=100,
        description="Number of messages to retrieve"
    )] = settings.default_messages_limit,
    offset_id: Annotated[int, Query(
        ge=0,
        description="Message ID for pagination (0 for first page)"
    )] = 0,
    date_from: Annotated[str | None, Query(
        description="Start date filter (ISO 8601 format)"
    )] = None,
    date_to: Annotated[str | None, Query(
        description="End date filter (ISO 8601 format)"
    )] = None,
    include_media: Annotated[bool, Query(
        description="Include media file information"
    )] = True,
    media_format: Annotated[str, Query(
        pattern="^(url|base64)$",
        description="Media format: 'url' or 'base64'"
    )] = "url"
):
    """
    Get messages from the configured Telegram channel.

    The channel is configured via TARGET_CHANNEL_ID environment variable.

    Features:
    - Pagination using offset_id
    - Date range filtering
    - Media file handling (URL or base64)
    - Metadata extraction (views, forwards, reactions)

    Query Parameters:
        limit: Number of messages per page (1-100, default: 20)
        offset_id: Message ID to start from (use next_offset_id from previous response)
        date_from: Filter messages from this date (ISO 8601)
        date_to: Filter messages until this date (ISO 8601)
        include_media: Whether to include media information
        media_format: Format for media files ('url' or 'base64')

    Returns:
        JSON with messages list and pagination info

    Examples:
        GET /api/v1/messages?limit=20&offset_id=0
        GET /api/v1/messages?limit=20&date_from=2026-01-01T00:00:00Z
        GET /api/v1/messages?limit=50&offset_id=12345&include_media=false
    """
    try:
        # Check authorization
        is_authorized = await telegram_manager.is_authorized()
        if not is_authorized:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Telegram. Please authenticate first."
            )

        # Validate limit
        if limit > settings.max_messages_per_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limit cannot exceed {settings.max_messages_per_request}"
            )

        # Parse dates if provided
        date_from_dt = None
        date_to_dt = None

        if date_from:
            try:
                from datetime import datetime
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date_from format: {str(e)}"
                )

        if date_to:
            try:
                from datetime import datetime
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date_to format: {str(e)}"
                )

        # Get configured channel ID
        target_channel_id = settings.target_channel_id

        # Get Telegram client
        client = telegram_manager.get_client()

        # Resolve channel ID to int and get title
        try:
            chat = await client.get_chat(target_channel_id)
            channel_id = chat.id
            channel_title = chat.title or str(channel_id)
        except Exception as e:
            from pyrogram.errors import ChannelPrivate, UsernameNotOccupied
            if isinstance(e, (ChannelPrivate, UsernameNotOccupied)):
                raise ChannelNotFoundError(target_channel_id)
            logger.error(f"Failed to resolve channel {target_channel_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resolve channel: {str(e)}"
            )

        # Create services
        message_service = MessageService(client)
        media_service = MediaService(client)

        # Fetch messages
        logger.info(
            f"Fetching messages from configured channel {channel_id} "
            f"(limit={limit}, offset_id={offset_id})"
        )

        messages, next_offset_id, has_more = await message_service.fetch_messages(
            channel_id=channel_id,
            limit=limit,
            offset_id=offset_id,
            date_from=date_from_dt,
            date_to=date_to_dt
        )

        # Format messages with media handling
        async def media_url_generator(message):
            """Generate media URL for a message."""
            if not include_media:
                return None

            # Get base URL from request
            base_url = str(request.base_url).rstrip('/')

            if media_format == "base64":
                # Return base64 encoded media
                return await media_service.get_media_base64(message, channel_id)
            else:
                # Return URL to media
                # Use lazy URL generation to avoid blocking download
                return media_service.get_lazy_media_url(
                    message,
                    channel_id,
                    base_url
                )

        formatted_messages = await message_service.format_messages(
            messages,
            include_media=include_media,
            media_url_generator=media_url_generator if include_media else None
        )

        # Build pagination info
        pagination = PaginationInfo(
            total_fetched=len(formatted_messages),
            next_offset_id=next_offset_id,
            has_more=has_more
        )

        logger.info(
            f"Retrieved {len(formatted_messages)} messages from channel {channel_id}"
        )

        return MessagesResponse(
            channel_id=channel_id,
            channel_title=channel_title,
            messages=formatted_messages,
            pagination=pagination
        )

    except ChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configured channel not accessible: {str(e.message)}"
        )

    except TelegramNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Telegram"
        )

    except Exception as e:
        logger.error(f"Failed to fetch messages from configured channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )
