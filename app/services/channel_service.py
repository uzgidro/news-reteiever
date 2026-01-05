"""Service for channel-related operations."""

import logging
from typing import List
from pyrogram import Client
from pyrogram.errors import ChannelPrivate, UsernameNotOccupied, UsernameInvalid

from app.core.exceptions import ChannelNotFoundError
from app.models.responses import ChannelInfo
from app.utils.formatters import format_channel

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing Telegram channel operations."""

    def __init__(self, client: Client):
        """
        Initialize channel service.

        Args:
            client: Pyrogram client instance
        """
        self.client = client

    async def get_joined_channels(self) -> List[ChannelInfo]:
        """
        Get list of channels the user is subscribed to.

        Returns:
            List of ChannelInfo objects

        Raises:
            TelegramNotAuthenticatedError: If not authenticated
        """
        try:
            channels = []

            # Get all dialogs (chats)
            async for dialog in self.client.get_dialogs():
                # Filter only channels (not groups or private chats)
                if dialog.chat.type.name in ["CHANNEL", "SUPERGROUP"]:
                    channel_info = format_channel(dialog.chat)
                    channels.append(channel_info)

            logger.info(f"Retrieved {len(channels)} joined channels")
            return channels

        except Exception as e:
            logger.error(f"Failed to get joined channels: {e}")
            raise

    async def get_channel_info(self, channel_id: int | str) -> ChannelInfo:
        """
        Get detailed information about a specific channel.

        Args:
            channel_id: Channel ID (int) or username (str)

        Returns:
            ChannelInfo object with channel details

        Raises:
            ChannelNotFoundError: If channel not found or not accessible
        """
        try:
            chat = await self.client.get_chat(channel_id)
            logger.info(f"Retrieved info for channel: {channel_id}")
            return format_channel(chat)

        except (ChannelPrivate, UsernameNotOccupied, UsernameInvalid) as e:
            logger.error(f"Channel {channel_id} not found or not accessible: {e}")
            raise ChannelNotFoundError(channel_id)

        except Exception as e:
            logger.error(f"Failed to get channel info for {channel_id}: {e}")
            raise

    async def is_channel_accessible(self, channel_id: int | str) -> bool:
        """
        Check if channel is accessible to the current user.

        Args:
            channel_id: Channel ID (int) or username (str)

        Returns:
            True if channel is accessible, False otherwise
        """
        try:
            await self.client.get_chat(channel_id)
            return True
        except (ChannelPrivate, UsernameNotOccupied, UsernameInvalid):
            return False
        except Exception as e:
            logger.error(f"Error checking channel accessibility: {e}")
            return False
