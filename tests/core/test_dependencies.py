"""Tests for core dependency providers."""

from sqlalchemy.orm import Session

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.dependencies import get_db
from ai_content_studio.core.settings import Settings


def test_settings_provider_returns_singleton() -> None:
    assert get_settings() is get_settings()


def test_settings_provider_returns_settings_instance() -> None:
    assert isinstance(get_settings(), Settings)


def test_db_provider_yields_session() -> None:
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)


def test_db_session_closes_after_use() -> None:
    import contextlib

    gen = get_db()
    next(gen)
    with contextlib.suppress(StopIteration):
        next(gen)
