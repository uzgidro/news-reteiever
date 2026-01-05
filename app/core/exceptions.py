"""Custom exceptions for the Telegram Channel Message Receiver application."""


class TelegramBaseException(Exception):
    """Base exception for all Telegram-related errors."""
    def __init__(self, message: str = "Telegram error occurred"):
        self.message = message
        super().__init__(self.message)


class TelegramNotAuthenticatedError(TelegramBaseException):
    """Raised when Telegram client is not authenticated."""
    def __init__(self, message: str = "Not authenticated with Telegram"):
        super().__init__(message)


class TelegramConnectionError(TelegramBaseException):
    """Raised when unable to connect to Telegram."""
    def __init__(self, message: str = "Failed to connect to Telegram"):
        super().__init__(message)


class ChannelNotFoundError(TelegramBaseException):
    """Raised when requested channel is not found or not accessible."""
    def __init__(self, channel_id: int | str = None, message: str = None):
        if message is None:
            if channel_id:
                message = f"Channel {channel_id} not found or not accessible"
            else:
                message = "Channel not found or not accessible"
        super().__init__(message)
        self.channel_id = channel_id


class MessageNotFoundError(TelegramBaseException):
    """Raised when requested message is not found."""
    def __init__(self, message_id: int = None, message: str = None):
        if message is None:
            if message_id:
                message = f"Message {message_id} not found"
            else:
                message = "Message not found"
        super().__init__(message)
        self.message_id = message_id


class MediaDownloadError(TelegramBaseException):
    """Raised when media file download fails."""
    def __init__(self, message: str = "Failed to download media file"):
        super().__init__(message)


class AuthenticationError(TelegramBaseException):
    """Raised when authentication process fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class TwoFactorAuthRequiredError(TelegramBaseException):
    """Raised when two-factor authentication is required."""
    def __init__(self, message: str = "Two-factor authentication required"):
        super().__init__(message)


class InvalidPhoneCodeError(TelegramBaseException):
    """Raised when provided phone code is invalid."""
    def __init__(self, message: str = "Invalid phone verification code"):
        super().__init__(message)


class InvalidPasswordError(TelegramBaseException):
    """Raised when provided 2FA password is invalid."""
    def __init__(self, message: str = "Invalid 2FA password"):
        super().__init__(message)
