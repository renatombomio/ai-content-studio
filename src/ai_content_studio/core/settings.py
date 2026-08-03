"""Application settings definition."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "The Cocoa Talk Studio"
    environment: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./data/studio.db"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"
    freepik_api_key: str | None = None
    pexels_api_key: str | None = None
