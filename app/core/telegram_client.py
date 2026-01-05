"""Telegram client manager for Pyrogram."""

import logging
from pathlib import Path
from typing import Optional

from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PasswordHashInvalid,
    FloodWait
)

from config import settings
from app.core.exceptions import (
    TelegramNotAuthenticatedError,
    TelegramConnectionError,
    TwoFactorAuthRequiredError,
    InvalidPhoneCodeError,
    InvalidPasswordError
)

logger = logging.getLogger(__name__)


class TelegramClientManager:
    """
    Singleton manager for Pyrogram Client.
    Handles connection lifecycle and authentication state.
    """

    _instance: Optional['TelegramClientManager'] = None
    _client: Optional[Client] = None
    _initialized: bool = False

    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the Telegram client manager."""
        if self._initialized:
            return

        # Ensure sessions directory exists
        sessions_path = Path(settings.sessions_dir)
        sessions_path.mkdir(parents=True, exist_ok=True)

        self._initialized = True
        logger.info("TelegramClientManager initialized")

    async def start(self) -> None:
        """
        Initialize and connect the Pyrogram client.

        Note: This only connects to Telegram if a session already exists.
        For first-time authentication, use the auth endpoints.
        """
        if self._client and self._client.is_connected:
            logger.info("Telegram client already connected")
            return

        try:
            self._client = Client(
                name=settings.session_name,
                api_id=settings.telegram_api_id,
                api_hash=settings.telegram_api_hash,
                workdir=settings.sessions_dir,
            )

            # Check if session file exists
            session_file = Path(settings.sessions_dir) / f"{settings.session_name}.session"

            if session_file.exists():
                # Session exists - connect without interactive prompts
                await self._client.connect()
                logger.info("Telegram client connected with existing session")
            else:
                # No session - just initialize the client object
                # Connection will happen during authentication
                logger.info("Telegram client initialized (no session found, authentication required)")

        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            # Don't raise exception - allow app to start without Telegram connection
            logger.warning("Application will start without Telegram connection")

    async def stop(self) -> None:
        """Stop the Pyrogram client."""
        if self._client and self._client.is_connected:
            try:
                await self._client.stop()
                logger.info("Telegram client stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram client: {e}")
        else:
            logger.info("Telegram client not connected, nothing to stop")

    def is_connected(self) -> bool:
        """Check if the client is connected to Telegram."""
        return self._client is not None and self._client.is_connected

    async def is_authorized(self) -> bool:
        """
        Check if the client is authorized (logged in).
        Returns True if session is valid and user is authenticated.
        """
        if not self.is_connected():
            return False

        try:
            # Try to get current user info to verify authentication
            me = await self._client.get_me()
            return me is not None
        except Exception as e:
            logger.debug(f"Authorization check failed: {e}")
            return False

    def get_client(self) -> Client:
        """
        Get the Pyrogram client instance.
        Raises TelegramNotAuthenticatedError if not connected.
        """
        if not self.is_connected():
            raise TelegramNotAuthenticatedError(
                "Telegram client not connected. Please start the client first."
            )
        return self._client

    async def send_code(self, phone: str) -> str:
        """
        Send verification code to the phone number.
        Returns phone_code_hash for verification.
        """
        try:
            # Ensure client is initialized
            if not self._client:
                await self.start()

            # Connect if not connected
            if not self._client.is_connected:
                await self._client.connect()

            sent_code = await self._client.send_code(phone)
            logger.info(f"Verification code sent to {phone}")
            return sent_code.phone_code_hash
        except Exception as e:
            logger.error(f"Failed to send verification code: {e}")
            raise

    async def sign_in(self, phone: str, code: str, phone_code_hash: str) -> bool:
        """
        Sign in with phone number and verification code.
        Returns True on success, raises exception on failure.
        """
        try:
            client = self.get_client()
            await client.sign_in(phone, phone_code_hash, code)
            logger.info(f"Successfully signed in with phone {phone}")
            return True

        except SessionPasswordNeeded:
            logger.info("Two-factor authentication is enabled")
            raise TwoFactorAuthRequiredError()

        except PhoneCodeInvalid:
            logger.error("Invalid phone verification code")
            raise InvalidPhoneCodeError()

        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            raise

    async def check_password(self, password: str) -> bool:
        """
        Complete 2FA authentication with password.
        Returns True on success, raises exception on failure.
        """
        try:
            client = self.get_client()
            await client.check_password(password)
            logger.info("Successfully authenticated with 2FA password")
            return True

        except PasswordHashInvalid:
            logger.error("Invalid 2FA password")
            raise InvalidPasswordError()

        except Exception as e:
            logger.error(f"2FA authentication failed: {e}")
            raise

    async def log_out(self) -> bool:
        """
        Log out from Telegram and invalidate session.
        Returns True on success.
        """
        try:
            client = self.get_client()
            await client.log_out()
            logger.info("Successfully logged out from Telegram")
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            raise

    async def get_me(self):
        """Get information about the current user."""
        client = self.get_client()
        return await client.get_me()


# Global singleton instance
telegram_manager = TelegramClientManager()
