"""Core module — configuration, logging, exceptions, and shared infrastructure."""

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.dependencies import DatabaseDep, SettingsDep, get_db
from ai_content_studio.core.exceptions import (
    AppError,
    AssetError,
    ConfigurationError,
    PipelineError,
    ProviderError,
    PublisherError,
    SchedulerError,
    StorageError,
    ValidationError,
    VideoError,
)
from ai_content_studio.core.logging import get_logger
from ai_content_studio.core.paths import (
    ASSETS,
    BRANDS,
    CACHE,
    DATA,
    DOCS,
    OUTPUT,
    PROJECTS,
    RENDERS,
    ROOT,
    SRC,
    TEMP,
)
from ai_content_studio.core.settings import Settings

__all__ = [
    "get_settings",
    "get_logger",
    "get_db",
    "Settings",
    "SettingsDep",
    "DatabaseDep",
    "AppError",
    "ConfigurationError",
    "ValidationError",
    "StorageError",
    "AssetError",
    "VideoError",
    "PublisherError",
    "SchedulerError",
    "PipelineError",
    "ProviderError",
    "ROOT",
    "SRC",
    "DOCS",
    "BRANDS",
    "DATA",
    "CACHE",
    "ASSETS",
    "PROJECTS",
    "RENDERS",
    "OUTPUT",
    "TEMP",
]
