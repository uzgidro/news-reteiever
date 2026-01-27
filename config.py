import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TelegramConfig:
    api_id: int
    api_hash: str
    target_channel_id: str | int


@dataclass
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@dataclass
class SessionConfig:
    name: str = "telegram_session"
    dir: str = "sessions"

    @property
    def path(self) -> Path:
        return Path(self.dir).resolve()


@dataclass
class MediaConfig:
    cache_dir: str = "media"
    cache_max_size_mb: int = 1000
    cache_ttl_hours: int = 24

    @property
    def cache_path(self) -> Path:
        return Path(self.cache_dir).resolve()


@dataclass
class ApiConfig:
    prefix: str = "/api/v1"
    max_messages_per_request: int = 100
    default_messages_limit: int = 20


@dataclass
class SecurityConfig:
    cors_origins: list[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["localhost:4200"]


@dataclass
class Settings:
    telegram: TelegramConfig
    app: AppConfig
    session: SessionConfig
    media: MediaConfig
    api: ApiConfig
    security: SecurityConfig

    # Backward compatibility properties
    @property
    def telegram_api_id(self) -> int:
        return self.telegram.api_id

    @property
    def telegram_api_hash(self) -> str:
        return self.telegram.api_hash

    @property
    def target_channel_id(self) -> str | int:
        return self.telegram.target_channel_id

    @property
    def app_host(self) -> str:
        return self.app.host

    @property
    def app_port(self) -> int:
        return self.app.port

    @property
    def app_debug(self) -> bool:
        return self.app.debug

    @property
    def session_name(self) -> str:
        return self.session.name

    @property
    def sessions_dir(self) -> str:
        return self.session.dir

    @property
    def sessions_path(self) -> Path:
        return self.session.path

    @property
    def media_cache_dir(self) -> str:
        return self.media.cache_dir

    @property
    def media_cache_path(self) -> Path:
        return self.media.cache_path

    @property
    def media_cache_max_size_mb(self) -> int:
        return self.media.cache_max_size_mb

    @property
    def media_cache_ttl_hours(self) -> int:
        return self.media.cache_ttl_hours

    @property
    def api_prefix(self) -> str:
        return self.api.prefix

    @property
    def max_messages_per_request(self) -> int:
        return self.api.max_messages_per_request

    @property
    def default_messages_limit(self) -> int:
        return self.api.default_messages_limit

    @property
    def cors_origins(self) -> list[str]:
        return self.security.cors_origins


def load_settings(config_path: str = "config/config.yaml") -> Settings:
    """Load settings from YAML config file."""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    telegram = TelegramConfig(
        api_id=data["telegram"]["api_id"],
        api_hash=data["telegram"]["api_hash"],
        target_channel_id=data["telegram"]["target_channel_id"],
    )

    app = AppConfig(
        host=data.get("app", {}).get("host", "0.0.0.0"),
        port=data.get("app", {}).get("port", 8000),
        debug=data.get("app", {}).get("debug", False),
    )

    session = SessionConfig(
        name=data.get("session", {}).get("name", "telegram_session"),
        dir=data.get("session", {}).get("dir", "sessions"),
    )

    media = MediaConfig(
        cache_dir=data.get("media", {}).get("cache_dir", "media"),
        cache_max_size_mb=data.get("media", {}).get("cache_max_size_mb", 1000),
        cache_ttl_hours=data.get("media", {}).get("cache_ttl_hours", 24),
    )

    api = ApiConfig(
        prefix=data.get("api", {}).get("prefix", "/api/v1"),
        max_messages_per_request=data.get("api", {}).get("max_messages_per_request", 100),
        default_messages_limit=data.get("api", {}).get("default_messages_limit", 20),
    )

    security = SecurityConfig(
        cors_origins=data.get("security", {}).get("cors_origins", ["localhost:4200"]),
    )

    return Settings(
        telegram=telegram,
        app=app,
        session=session,
        media=media,
        api=api,
        security=security,
    )


# Global settings instance
settings = load_settings()
