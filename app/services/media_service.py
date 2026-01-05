"""Service for media file handling and caching."""

import logging
import os
from pathlib import Path
from typing import Optional
import base64

from pyrogram import Client
from pyrogram.types import Message
import aiofiles

from config import settings
from app.core.exceptions import MediaDownloadError

logger = logging.getLogger(__name__)


class MediaService:
    """Service for downloading and caching media files."""

    def __init__(self, client: Client):
        """
        Initialize media service.

        Args:
            client: Pyrogram client instance
        """
        self.client = client
        self.cache_dir = Path(settings.media_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_media_cache_path(
        self,
        channel_id: int,
        message_id: int,
        file_name: str
    ) -> Path:
        """
        Get the cache path for a media file.

        Args:
            channel_id: Channel ID
            message_id: Message ID
            file_name: File name

        Returns:
            Path object for the cached file
        """
        # Create directory structure: media/{channel_id}/{message_id}/
        message_dir = self.cache_dir / str(abs(channel_id)) / str(message_id)
        message_dir.mkdir(parents=True, exist_ok=True)

        return message_dir / file_name

    def _get_file_extension(self, message: Message) -> str:
        """
        Get appropriate file extension for media type.

        Args:
            message: Pyrogram Message object

        Returns:
            File extension string
        """
        if message.photo:
            return ".jpg"
        elif message.video:
            return message.video.file_name or ".mp4"
        elif message.audio:
            return message.audio.file_name or ".mp3"
        elif message.voice:
            return ".ogg"
        elif message.document:
            return message.document.file_name or ".bin"
        elif message.animation:
            return message.animation.file_name or ".gif"
        elif message.video_note:
            return ".mp4"
        else:
            return ".bin"

    async def download_media(
        self,
        message: Message,
        channel_id: int
    ) -> Optional[Path]:
        """
        Download media from a message and cache it.

        Args:
            message: Pyrogram Message object with media
            channel_id: Channel ID for organizing cache

        Returns:
            Path to downloaded file, or None if no media

        Raises:
            MediaDownloadError: If download fails
        """
        if not message.media:
            return None

        try:
            # Generate file name
            file_ext = self._get_file_extension(message)
            if isinstance(file_ext, str) and not file_ext.startswith('.'):
                file_name = file_ext
            else:
                file_name = f"{message.id}{file_ext}"

            # Get cache path
            cache_path = self._get_media_cache_path(
                channel_id,
                message.id,
                file_name
            )

            # Check if already cached
            if cache_path.exists():
                logger.debug(f"Media already cached: {cache_path}")
                return cache_path

            # Download media
            logger.info(f"Downloading media for message {message.id}")
            downloaded_path = await self.client.download_media(
                message,
                file_name=str(cache_path)
            )

            if not downloaded_path:
                raise MediaDownloadError(
                    f"Failed to download media for message {message.id}"
                )

            logger.info(f"Media downloaded successfully: {downloaded_path}")
            return Path(downloaded_path)

        except Exception as e:
            logger.error(f"Media download failed: {e}")
            raise MediaDownloadError(f"Media download failed: {str(e)}")

    async def get_media_url(
        self,
        message: Message,
        channel_id: int,
        base_url: str = ""
    ) -> Optional[str]:
        """
        Get URL for media file (downloads if not cached).

        Args:
            message: Pyrogram Message object
            channel_id: Channel ID
            base_url: Base URL for constructing media URLs

        Returns:
            URL string or None if no media
        """
        if not message.media:
            return None

        try:
            cache_path = await self.download_media(message, channel_id)

            if not cache_path:
                return None

            # Generate relative path from cache_dir
            relative_path = cache_path.relative_to(self.cache_dir)

            # Construct URL
            # Format: /media/{channel_id}/{message_id}/{filename}
            url_path = str(relative_path).replace('\\', '/')
            media_url = f"{base_url}/media/{url_path}"

            return media_url

        except Exception as e:
            logger.error(f"Failed to get media URL: {e}")
            return None

    def get_lazy_media_url(
        self,
        message: Message,
        channel_id: int,
        base_url: str
    ) -> Optional[str]:
        """
        Get URL for media file that triggers download on access.

        Args:
            message: Pyrogram Message object
            channel_id: Channel ID
            base_url: Base URL for constructing media URLs

        Returns:
            URL string or None if no media
        """
        if not message.media:
            return None

        try:
            file_ext = self._get_file_extension(message)
            if isinstance(file_ext, str) and not file_ext.startswith('.'):
                file_name = file_ext
            else:
                file_name = f"{message.id}{file_ext}"

            # Construct URL for the download endpoint
            # Format: /api/v1/media/download/{channel_id}/{message_id}/{filename}
            media_url = f"{base_url}/api/v1/media/download/{channel_id}/{message.id}/{file_name}"
            
            return media_url

        except Exception as e:
            logger.error(f"Failed to generate lazy media URL: {e}")
            return None

    async def get_media_base64(
        self,
        message: Message,
        channel_id: int
    ) -> Optional[str]:
        """
        Get media file as base64 encoded string.

        Args:
            message: Pyrogram Message object
            channel_id: Channel ID

        Returns:
            Base64 encoded string or None

        Warning:
            This can be memory-intensive for large files.
            Recommended only for small images.
        """
        if not message.media:
            return None

        try:
            cache_path = await self.download_media(message, channel_id)

            if not cache_path or not cache_path.exists():
                return None

            # Read file and encode to base64
            async with aiofiles.open(cache_path, 'rb') as f:
                file_data = await f.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
                return base64_data

        except Exception as e:
            logger.error(f"Failed to encode media to base64: {e}")
            return None

    def get_cached_media_path(
        self,
        channel_id: int,
        message_id: int,
        file_name: str
    ) -> Optional[Path]:
        """
        Get path to cached media file if it exists.

        Args:
            channel_id: Channel ID
            message_id: Message ID
            file_name: File name

        Returns:
            Path if file exists, None otherwise
        """
        cache_path = self._get_media_cache_path(channel_id, message_id, file_name)

        if cache_path.exists():
            return cache_path

        return None

    def clear_cache(self) -> int:
        """
        Clear all cached media files.

        Returns:
            Number of files deleted
        """
        deleted_count = 0

        try:
            for file_path in self.cache_dir.rglob('*'):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1

            logger.info(f"Cleared {deleted_count} cached media files")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return deleted_count
