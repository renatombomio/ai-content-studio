"""Tests for Publisher interface."""

from pathlib import Path

import pytest

from ai_content_studio.publisher.interface import Publisher
from ai_content_studio.shared.models import Publication, PublicationStatus


def _make_publication(**kwargs: object) -> Publication:
    defaults: dict[str, object] = {
        "platform": "tiktok",
        "video_path": Path("/tmp/video.mp4"),
        "title": "The Origin of Cocoa",
        "caption": "Did you know chocolate has a 3,000-year history?",
        "hashtags": ["#CocoaTalk"],
    }
    defaults.update(kwargs)
    return Publication(**defaults)  # type: ignore[arg-type]


def test_publisher_is_abstract() -> None:
    with pytest.raises(TypeError):
        Publisher()  # type: ignore[abstract]


def test_publish_must_be_implemented() -> None:
    class IncompletePublisher(Publisher):
        pass

    with pytest.raises(TypeError):
        IncompletePublisher()  # type: ignore[abstract]


def test_concrete_publisher_is_instantiable() -> None:
    class ConcretePublisher(Publisher):
        def publish(self, publication: Publication) -> Publication:
            return publication

    publisher = ConcretePublisher()
    assert isinstance(publisher, Publisher)


def test_publish_returns_publication() -> None:
    class ConcretePublisher(Publisher):
        def publish(self, publication: Publication) -> Publication:
            return publication

    pub = _make_publication()
    result = ConcretePublisher().publish(pub)
    assert isinstance(result, Publication)


def test_publish_can_update_status() -> None:
    class ConcretePublisher(Publisher):
        def publish(self, publication: Publication) -> Publication:
            return publication.model_copy(update={"status": PublicationStatus.PUBLISHED})

    pub = _make_publication()
    result = ConcretePublisher().publish(pub)
    assert result.status == PublicationStatus.PUBLISHED


def test_publish_can_update_tiktok_identifiers() -> None:
    class ConcretePublisher(Publisher):
        def publish(self, publication: Publication) -> Publication:
            return publication.model_copy(update={
                "publish_id": "pid-123",
                "external_id": "ext-456",
            })

    pub = _make_publication()
    result = ConcretePublisher().publish(pub)
    assert result.publish_id == "pid-123"
    assert result.external_id == "ext-456"
