"""Channels API routes."""

import logging
from fastapi import APIRouter, HTTPException, status, Path

from app.core.telegram_client import telegram_manager
from app.core.exceptions import (
    TelegramNotAuthenticatedError,
    ChannelNotFoundError
)
from app.services.channel_service import ChannelService
from app.models.responses import ChannelsListResponse, ChannelInfo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/joined",
    response_model=ChannelsListResponse,
    summary="Get joined channels",
    description="Get list of channels the authenticated user is subscribed to"
)
async def get_joined_channels():
    """
    Get list of all channels the authenticated user has joined.

    Returns information about each channel including ID, title,
    username, and participant count.

    Requires authentication.
    """
    try:
        # Check authorization
        is_authorized = await telegram_manager.is_authorized()
        if not is_authorized:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Telegram. Please authenticate first."
            )

        # Get Telegram client
        client = telegram_manager.get_client()

        # Create service and fetch channels
        channel_service = ChannelService(client)
        channels = await channel_service.get_joined_channels()

        logger.info(f"Retrieved {len(channels)} joined channels")

        return ChannelsListResponse(channels=channels)

    except TelegramNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Telegram"
        )

    except Exception as e:
        logger.error(f"Failed to get joined channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channels: {str(e)}"
        )


@router.get(
    "/{channel_id}/info",
    response_model=ChannelInfo,
    summary="Get channel information",
    description="Get detailed information about a specific channel"
)
async def get_channel_info(
    channel_id: int = Path(..., description="Channel ID or username")
):
    """
    Get detailed information about a specific channel.

    Args:
        channel_id: Channel ID (negative integer) or username (string)

    Returns:
        Detailed channel information including title, description,
        participant count, and more.

    Requires:
        - Authentication
        - Access to the channel (must be a member or channel must be public)
    """
    try:
        # Check authorization
        is_authorized = await telegram_manager.is_authorized()
        if not is_authorized:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Telegram"
            )

        # Get Telegram client
        client = telegram_manager.get_client()

        # Create service and fetch channel info
        channel_service = ChannelService(client)
        channel_info = await channel_service.get_channel_info(channel_id)

        logger.info(f"Retrieved info for channel {channel_id}")

        return channel_info

    except ChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.message)
        )

    except TelegramNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Telegram"
        )

    except Exception as e:
        logger.error(f"Failed to get channel info for {channel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channel information: {str(e)}"
        )
