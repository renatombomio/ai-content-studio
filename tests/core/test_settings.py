"""Tests for core settings and config."""

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "The Cocoa Talk Studio"
    assert settings.environment == "development"
    assert settings.debug is True


def test_get_settings_returns_settings_instance() -> None:
    assert isinstance(get_settings(), Settings)


def test_get_settings_is_singleton() -> None:
    assert get_settings() is get_settings()
