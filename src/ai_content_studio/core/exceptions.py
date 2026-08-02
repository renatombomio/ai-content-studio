"""Application-wide exception hierarchy."""


class AppError(Exception):
    """Base exception for all application errors."""


class ConfigurationError(AppError):
    """Raised when the application configuration is invalid."""


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class PipelineError(AppError):
    """Raised when a pipeline stage fails."""
