"""Application-wide exception hierarchy rooted at AppError."""


class AppError(Exception):
    """Base exception for all application errors."""


class ConfigurationError(AppError):
    """Raised when the application is misconfigured or a required setting is missing."""


class ValidationError(AppError):
    """Raised when input data fails validation."""


class StorageError(AppError):
    """Raised when a filesystem or storage operation fails."""


class AssetError(AppError):
    """Raised when an asset cannot be found, downloaded, or resolved."""


class VideoError(AppError):
    """Raised when video assembly or rendering fails."""


class PublisherError(AppError):
    """Raised when publishing to TikTok fails."""


class SchedulerError(AppError):
    """Raised when the scheduler cannot trigger or manage a job."""


class PipelineError(AppError):
    """Raised when a pipeline stage fails and execution cannot continue."""
