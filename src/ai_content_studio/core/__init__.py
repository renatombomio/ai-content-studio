"""Core module — configuration, logging, exceptions, and shared infrastructure."""

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import (
    AppError,
    ConfigurationError,
    NotFoundError,
    PipelineError,
)
from ai_content_studio.core.logging import get_logger
from ai_content_studio.core.paths import BRANDS, DOCS, ROOT, SRC
from ai_content_studio.core.settings import Settings

__all__ = [
    "get_settings",
    "get_logger",
    "Settings",
    "AppError",
    "ConfigurationError",
    "NotFoundError",
    "PipelineError",
    "ROOT",
    "SRC",
    "BRANDS",
    "DOCS",
]
