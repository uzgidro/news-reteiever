"""Utilities for formatting data from Pyrogram to API response models."""

from typing import Optional, List
from pyrogram.types import Message, Chat, User
from pyrogram import enums

from app.models.responses import (
    MessageResponse,
    MediaInfo,
    AuthorInfo,
    ReactionInfo,
    ChannelInfo
)


def format_author(user: Optional[User]) -> Optional[AuthorInfo]:
    """Format Pyrogram User to AuthorInfo model."""
    if not user:
        return None

    return AuthorInfo(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )


def format_reactions(message: Message) -> Optional[List[ReactionInfo]]:
    """Extract and format reactions from a message."""
    if not message.reactions or not message.reactions.reactions:
        return None

    reactions = []
    for reaction in message.reactions.reactions:
        if hasattr(reaction, 'emoji') and hasattr(reaction, 'count'):
            reactions.append(ReactionInfo(
                emoji=reaction.emoji,
                count=reaction.count
            ))

    return reactions if reactions else None


def get_media_type(message: Message) -> Optional[str]:
    """Determine media type from message."""
    if message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.audio:
        return "audio"
    elif message.voice:
        return "voice"
    elif message.document:
        return "document"
    elif message.sticker:
        return "sticker"
    elif message.animation:
        return "animation"
    elif message.video_note:
        return "video_note"
    return None


def format_media(message: Message, media_url: Optional[str] = None) -> Optional[MediaInfo]:
    """Format media information from a message."""
    media_type = get_media_type(message)

    if not media_type:
        return None

    media_info = MediaInfo(type=media_type, url=media_url)

    # Photo
    if message.photo:
        media_info.file_size = message.photo.file_size
        media_info.width = message.photo.width
        media_info.height = message.photo.height
        if message.photo.thumbs:
            # Thumbnail URL will be handled separately if needed
            pass

    # Video
    elif message.video:
        media_info.file_size = message.video.file_size
        media_info.mime_type = message.video.mime_type
        media_info.duration = message.video.duration
        media_info.width = message.video.width
        media_info.height = message.video.height
        media_info.file_name = message.video.file_name

    # Audio
    elif message.audio:
        media_info.file_size = message.audio.file_size
        media_info.mime_type = message.audio.mime_type
        media_info.duration = message.audio.duration
        media_info.file_name = message.audio.file_name

    # Voice
    elif message.voice:
        media_info.file_size = message.voice.file_size
        media_info.mime_type = message.voice.mime_type
        media_info.duration = message.voice.duration

    # Document
    elif message.document:
        media_info.file_size = message.document.file_size
        media_info.mime_type = message.document.mime_type
        media_info.file_name = message.document.file_name

    # Animation (GIF)
    elif message.animation:
        media_info.file_size = message.animation.file_size
        media_info.mime_type = message.animation.mime_type
        media_info.width = message.animation.width
        media_info.height = message.animation.height
        media_info.file_name = message.animation.file_name

    return media_info


def format_message(message: Message, media_url: Optional[str] = None) -> MessageResponse:
    """Format Pyrogram Message to MessageResponse model."""
    return MessageResponse(
        id=message.id,
        text=message.text or message.caption,
        date=message.date,
        views=message.views,
        forwards=message.forwards,
        reactions=format_reactions(message),
        author=format_author(message.from_user) if message.from_user else None,
        media=format_media(message, media_url),
        reply_to_message_id=message.reply_to_message_id,
        edit_date=message.edit_date,
        has_protected_content=message.has_protected_content or False
    )


def format_channel(chat: Chat) -> ChannelInfo:
    """Format Pyrogram Chat to ChannelInfo model."""
    return ChannelInfo(
        id=chat.id,
        username=chat.username,
        title=chat.title,
        description=chat.description,
        participants_count=chat.members_count,
        photo_url=None  # Will be handled separately if needed
    )
