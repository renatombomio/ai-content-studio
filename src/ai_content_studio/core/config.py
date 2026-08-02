"""Configuration loader."""

from functools import lru_cache

from ai_content_studio.core.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
