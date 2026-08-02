"""Centralized logging configuration."""

import logging

_configured = False

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def _configure() -> None:
    global _configured
    if _configured:
        return

    from ai_content_studio.core.config import get_settings

    level = logging.DEBUG if get_settings().debug else logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(_FORMATTER)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, configuring the root logger on first call."""
    _configure()
    return logging.getLogger(name)
