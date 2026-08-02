"""Tests for core logging."""

import logging
from unittest.mock import patch

from ai_content_studio.core.logging import get_logger
from ai_content_studio.core.settings import Settings


def test_get_logger_returns_logger() -> None:
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)


def test_same_name_returns_same_logger() -> None:
    assert get_logger("test.same") is get_logger("test.same")


def test_level_follows_debug_true() -> None:
    with (
        patch("ai_content_studio.core.logging._configured", False),
        patch("ai_content_studio.core.config.get_settings", return_value=Settings(debug=True)),
    ):
        import ai_content_studio.core.logging as log_mod
        log_mod._configured = False
        get_logger("test.debug")
        assert logging.getLogger().level == logging.DEBUG


def test_level_follows_debug_false() -> None:
    with (
        patch("ai_content_studio.core.logging._configured", False),
        patch("ai_content_studio.core.config.get_settings", return_value=Settings(debug=False)),
    ):
        import ai_content_studio.core.logging as log_mod
        log_mod._configured = False
        get_logger("test.info")
        assert logging.getLogger().level == logging.INFO
