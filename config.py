from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # Telegram API Credentials
    telegram_api_id: int
    telegram_api_hash: str

    # Target Channel (the single channel this microservice monitors)
    target_channel_id: str | int

    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False

    # Session Settings
    session_name: str = "telegram_session"
    sessions_dir: str = "sessions"

    # Media Settings
    media_cache_dir: str = "media"
    media_cache_max_size_mb: int = 1000
    media_cache_ttl_hours: int = 24

    # API Settings
    api_prefix: str = "/api/v1"
    max_messages_per_request: int = 100
    default_messages_limit: int = 20

    # Security
    cors_origins: list[str] = ["neptun.speedwagon.uz"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def sessions_path(self) -> Path:
        """Get absolute path to sessions directory."""
        return Path(self.sessions_dir).resolve()

    @property
    def media_cache_path(self) -> Path:
        """Get absolute path to media cache directory."""
        return Path(self.media_cache_dir).resolve()


# Global settings instance
settings = Settings()
