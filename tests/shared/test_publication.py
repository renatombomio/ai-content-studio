"""Tests for the Publication domain model."""

from datetime import UTC, datetime
from pathlib import Path

from ai_content_studio.shared.models import Publication, PublicationStatus


def _make_publication(**kwargs: object) -> Publication:
    defaults: dict[str, object] = {
        "platform": "tiktok",
        "video_path": Path("/tmp/video.mp4"),
        "title": "The Origin of Cocoa",
        "caption": "Did you know chocolate has a 3,000-year history?",
        "hashtags": ["#CocoaTalk", "#Chocolate"],
    }
    defaults.update(kwargs)
    return Publication(**defaults)  # type: ignore[arg-type]


# --- PublicationStatus ---


def test_status_values() -> None:
    assert PublicationStatus.PENDING == "pending"
    assert PublicationStatus.PROCESSING == "processing"
    assert PublicationStatus.PUBLISHED == "published"
    assert PublicationStatus.FAILED == "failed"


def test_status_is_str() -> None:
    assert isinstance(PublicationStatus.PENDING, str)


def test_status_lifecycle_order() -> None:
    statuses = [
        PublicationStatus.PENDING,
        PublicationStatus.PROCESSING,
        PublicationStatus.PUBLISHED,
    ]
    assert statuses == ["pending", "processing", "published"]


# --- Publication creation ---


def test_publication_creation() -> None:
    pub = _make_publication()
    assert pub.platform == "tiktok"
    assert pub.title == "The Origin of Cocoa"
    assert pub.caption == "Did you know chocolate has a 3,000-year history?"
    assert pub.hashtags == ["#CocoaTalk", "#Chocolate"]
    assert pub.video_path == Path("/tmp/video.mp4")


def test_publication_id_auto_generated() -> None:
    p1 = _make_publication()
    p2 = _make_publication()
    assert p1.id != p2.id


def test_publication_id_is_str() -> None:
    pub = _make_publication()
    assert isinstance(pub.id, str)
    assert len(pub.id) > 0


# --- Default status ---


def test_publication_default_status_is_pending() -> None:
    pub = _make_publication()
    assert pub.status == PublicationStatus.PENDING


# --- Optional fields ---


def test_publication_optional_fields_default_none() -> None:
    pub = _make_publication()
    assert pub.publish_id is None
    assert pub.external_id is None
    assert pub.url is None
    assert pub.published_at is None


def test_publication_optional_fields_accepted() -> None:
    dt = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    pub = _make_publication(
        publish_id="tiktok-publish-abc123",
        external_id="7391234567890",
        url="https://www.tiktok.com/@cocoa/video/7391234567890",
        published_at=dt,
    )
    assert pub.publish_id == "tiktok-publish-abc123"
    assert pub.external_id == "7391234567890"
    assert pub.url == "https://www.tiktok.com/@cocoa/video/7391234567890"
    assert pub.published_at == dt


# --- Status transitions ---


def test_publication_status_set_to_processing() -> None:
    pub = _make_publication(status=PublicationStatus.PROCESSING)
    assert pub.status == PublicationStatus.PROCESSING


def test_publication_status_set_to_published() -> None:
    pub = _make_publication(status=PublicationStatus.PUBLISHED)
    assert pub.status == PublicationStatus.PUBLISHED


def test_publication_status_set_to_failed() -> None:
    pub = _make_publication(status=PublicationStatus.FAILED)
    assert pub.status == PublicationStatus.FAILED


# --- Serialization ---


def test_publication_model_dump_contains_all_fields() -> None:
    pub = _make_publication()
    data = pub.model_dump()
    for field in ("id", "platform", "video_path", "title", "caption", "hashtags",
                  "status", "publish_id", "external_id", "url", "published_at"):
        assert field in data


def test_publication_model_dump_status_as_str() -> None:
    pub = _make_publication()
    data = pub.model_dump()
    assert data["status"] == "pending"


def test_publication_model_dump_hashtags() -> None:
    pub = _make_publication(hashtags=["#a", "#b", "#c"])
    data = pub.model_dump()
    assert data["hashtags"] == ["#a", "#b", "#c"]


def test_publication_model_dump_none_fields() -> None:
    pub = _make_publication()
    data = pub.model_dump()
    assert data["publish_id"] is None
    assert data["external_id"] is None
    assert data["url"] is None
    assert data["published_at"] is None
