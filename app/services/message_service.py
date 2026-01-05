"""Service for message-related operations."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import ChannelPrivate

from app.core.exceptions import ChannelNotFoundError, MessageNotFoundError
from app.models.responses import MessageResponse
from app.utils.formatters import format_message

logger = logging.getLogger(__name__)


class MessageService:
    """Service for fetching and processing Telegram messages."""

    def __init__(self, client: Client):
        """
        Initialize message service.

        Args:
            client: Pyrogram client instance
        """
        self.client = client

    async def fetch_messages(
        self,
        channel_id: int | str,
        limit: int = 20,
        offset_id: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Tuple[List[Message], Optional[int], bool]:
        """
        Fetch messages from a channel with pagination and date filtering.

        Args:
            channel_id: Channel ID or username
            limit: Number of messages to fetch
            offset_id: Message ID to use as offset for pagination
            date_from: Filter messages from this date
            date_to: Filter messages until this date

        Returns:
            Tuple of (messages list, next_offset_id, has_more)

        Raises:
            ChannelNotFoundError: If channel not accessible
        """
        try:
            messages = []
            fetched_count = 0

            # Iterate through chat history
            async for message in self.client.get_chat_history(
                channel_id,
                limit=limit,
                offset_id=offset_id if offset_id > 0 else 0
            ):
                fetched_count += 1

                # Apply date filtering
                if date_from and message.date < date_from:
                    # Messages are in descending order, so we can break early
                    break

                if date_to and message.date > date_to:
                    # Skip messages that are too new
                    continue

                # Both conditions met, add to results
                if (not date_from or message.date >= date_from) and \
                   (not date_to or message.date <= date_to):
                    messages.append(message)

                # Stop if we've collected enough messages
                if len(messages) >= limit:
                    break

            # Calculate next offset and has_more flag
            next_offset_id = messages[-1].id if messages else None
            has_more = fetched_count >= limit

            logger.info(
                f"Fetched {len(messages)} messages from channel {channel_id} "
                f"(offset_id={offset_id}, limit={limit})"
            )

            return messages, next_offset_id, has_more

        except ChannelPrivate:
            logger.error(f"Channel {channel_id} is private or not accessible")
            raise ChannelNotFoundError(channel_id)

        except Exception as e:
            logger.error(f"Failed to fetch messages from {channel_id}: {e}")
            raise

    async def get_message_by_id(
        self,
        channel_id: int | str,
        message_id: int
    ) -> Message:
        """
        Get a specific message by its ID.

        Args:
            channel_id: Channel ID or username
            message_id: Message ID

        Returns:
            Pyrogram Message object

        Raises:
            MessageNotFoundError: If message not found
            ChannelNotFoundError: If channel not accessible
        """
        try:
            messages = await self.client.get_messages(
                channel_id,
                message_ids=message_id
            )

            if not messages or messages.empty:
                raise MessageNotFoundError(message_id)

            logger.info(f"Retrieved message {message_id} from channel {channel_id}")
            return messages

        except ChannelPrivate:
            logger.error(f"Channel {channel_id} is private or not accessible")
            raise ChannelNotFoundError(channel_id)

        except Exception as e:
            logger.error(
                f"Failed to get message {message_id} from {channel_id}: {e}"
            )
            raise

    async def format_messages(
        self,
        messages: List[Message],
        include_media: bool = True,
        media_url_generator = None
    ) -> List[MessageResponse]:
        """
        Format raw Pyrogram messages to MessageResponse models.

        Args:
            messages: List of Pyrogram Message objects
            include_media: Whether to include media information
            media_url_generator: Optional callable to generate media URLs

        Returns:
            List of formatted MessageResponse objects
        """
        formatted_messages = []

        for message in messages:
            # Generate media URL if needed
            media_url = None
            if include_media and media_url_generator and message.media:
                try:
                    media_url = await media_url_generator(message)
                except Exception as e:
                    logger.warning(f"Failed to generate media URL for message {message.id}: {e}")

            formatted_message = format_message(message, media_url)
            formatted_messages.append(formatted_message)

        return formatted_messages

    async def get_channel_title(self, channel_id: int | str) -> str:
        """
        Get the title of a channel.

        Args:
            channel_id: Channel ID or username

        Returns:
            Channel title

        Raises:
            ChannelNotFoundError: If channel not accessible
        """
        try:
            chat = await self.client.get_chat(channel_id)
            return chat.title or str(channel_id)

        except ChannelPrivate:
            raise ChannelNotFoundError(channel_id)

        except Exception as e:
            logger.error(f"Failed to get channel title for {channel_id}: {e}")
            return str(channel_id)
