"""Tests for core exception hierarchy."""

import pytest

from ai_content_studio.core.exceptions import (
    AppError,
    AssetError,
    ConfigurationError,
    PipelineError,
    PublisherError,
    SchedulerError,
    StorageError,
    ValidationError,
    VideoError,
)

ALL_EXCEPTIONS = [
    ConfigurationError,
    ValidationError,
    StorageError,
    AssetError,
    VideoError,
    PublisherError,
    SchedulerError,
    PipelineError,
]


def test_all_inherit_from_app_error() -> None:
    for exc_class in ALL_EXCEPTIONS:
        assert issubclass(exc_class, AppError), f"{exc_class} does not inherit from AppError"


def test_all_inherit_from_exception() -> None:
    for exc_class in ALL_EXCEPTIONS:
        assert issubclass(exc_class, Exception)


def test_isinstance_via_app_error() -> None:
    for exc_class in ALL_EXCEPTIONS:
        instance = exc_class("test")
        assert isinstance(instance, AppError)
        assert isinstance(instance, exc_class)


def test_message_propagation() -> None:
    for exc_class in ALL_EXCEPTIONS:
        msg = f"error in {exc_class.__name__}"
        exc = exc_class(msg)
        assert str(exc) == msg


def test_can_be_raised_and_caught_as_app_error() -> None:
    for exc_class in ALL_EXCEPTIONS:
        with pytest.raises(AppError):
            raise exc_class("raised")
