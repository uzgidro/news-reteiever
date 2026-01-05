"""Media API routes."""

import logging
from typing import Annotated
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Path as PathParam
from fastapi.responses import FileResponse

from app.core.telegram_client import telegram_manager
from app.core.exceptions import (
    TelegramNotAuthenticatedError,
    ChannelNotFoundError,
    MessageNotFoundError,
    MediaDownloadError
)
from app.services.message_service import MessageService
from app.services.media_service import MediaService
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/download/{channel_id}/{message_id}/{file_name}",
    summary="Download media file",
    description="Download media file for a specific message. Downloads from Telegram if not cached."
)
async def download_media(
    channel_id: Annotated[int, PathParam(description="Channel ID")],
    message_id: Annotated[int, PathParam(description="Message ID")],
    file_name: Annotated[str, PathParam(description="File name")]
):
    """
    Download and serve a media file.

    If the file is already cached, it is served immediately.
    If not, it is downloaded from Telegram first.
    """
    try:
        # Check authorization
        if not await telegram_manager.is_authorized():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Telegram"
            )

        client = telegram_manager.get_client()
        media_service = MediaService(client)
        message_service = MessageService(client)

        # Check cache first (optimization to avoid fetching message if file exists)
        cached_path = media_service.get_cached_media_path(channel_id, message_id, file_name)
        if cached_path and cached_path.exists():
            return FileResponse(cached_path)

        # If not cached, we need to fetch the message to download media
        try:
            message = await message_service.get_message_by_id(channel_id, message_id)
        except (MessageNotFoundError, ChannelNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message or channel not found"
            )

        # Download media
        try:
            file_path = await media_service.download_media(message, channel_id)
        except MediaDownloadError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download media file"
            )
            
        if not file_path or not file_path.exists():
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found"
            )

        return FileResponse(file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving media file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
