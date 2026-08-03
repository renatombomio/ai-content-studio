"""Tests for PublicationService."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from ai_content_studio.core.exceptions import PublisherError
from ai_content_studio.publisher.auth import OAuthToken
from ai_content_studio.publisher.service import _STATUS_URL, PublicationService
from ai_content_studio.shared.models import Publication, PublicationStatus

_TOKEN = OAuthToken(
    access_token="act-abc123",
    refresh_token="rft-xyz",
    expires_at=datetime(2026, 8, 4, 10, 0, tzinfo=UTC),
)

_PROCESSING_BODY = {
    "data": {"status": "PROCESSING_UPLOAD"},
    "error": {"code": "ok", "message": "", "log_id": "x"},
}

_COMPLETE_BODY = {
    "data": {
        "status": "PUBLISH_COMPLETE",
        "publicaly_available_post_id": "7391234567890",
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}

_FAILED_BODY = {
    "data": {"status": "FAILED", "fail_reason": "content_violation"},
    "error": {"code": "ok", "message": "", "log_id": "x"},
}


@pytest.fixture
def video_file(tmp_path: Path) -> Path:
    path = tmp_path / "video.mp4"
    path.write_bytes(b"x" * 50)
    return path


@pytest.fixture
def publication(video_file: Path) -> Publication:
    return Publication(
        platform="tiktok",
        video_path=video_file,
        title="The Origin of Cocoa",
        caption="Did you know?",
        hashtags=["#CocoaTalk"],
        publish_id="pub-abc123",
        status=PublicationStatus.PROCESSING,
    )


@pytest.fixture
def mock_oauth() -> MagicMock:
    oauth = MagicMock()
    oauth.exchange_code.return_value = _TOKEN
    return oauth


@pytest.fixture
def mock_publisher(publication: Publication) -> MagicMock:
    publisher = MagicMock()
    publisher.publish.return_value = publication
    return publisher


def _make_service(
    mock_oauth: MagicMock,
    mock_publisher: MagicMock,
    poll_interval: float = 0.0,
    poll_timeout: float = 30.0,
) -> PublicationService:
    return PublicationService(
        oauth=mock_oauth,
        publisher=mock_publisher,
        poll_interval=poll_interval,
        poll_timeout=poll_timeout,
    )


def _ok(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _http_error() -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="HTTP 500", request=MagicMock(), response=MagicMock(status_code=500)
    )
    return resp


# --- OAuth exchange ---


def test_publish_calls_exchange_code(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        svc.publish(publication, "mycode")
    mock_oauth.exchange_code.assert_called_once_with("mycode")


def test_publish_passes_token_to_publisher(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        svc.publish(publication, "mycode")
    mock_publisher.publish.assert_called_once_with(publication, _TOKEN)


# --- upload ---


def test_publish_calls_publisher(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        svc.publish(publication, "mycode")
    mock_publisher.publish.assert_called_once()


# --- polling ---


def test_publish_polls_status_endpoint(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)) as mock_post, \
         patch("ai_content_studio.publisher.service.time.sleep"):
        svc.publish(publication, "mycode")
    status_calls = [c for c in mock_post.call_args_list if c.args[0] == _STATUS_URL]
    assert len(status_calls) >= 1


def test_publish_sends_publish_id_in_poll(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)) as mock_post, \
         patch("ai_content_studio.publisher.service.time.sleep"):
        svc.publish(publication, "mycode")
    status_call = next(c for c in mock_post.call_args_list if c.args[0] == _STATUS_URL)
    assert status_call.kwargs["json"]["publish_id"] == "pub-abc123"


def test_publish_continues_polling_while_processing(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    side_effects = [_ok(_PROCESSING_BODY), _ok(_PROCESSING_BODY), _ok(_COMPLETE_BODY)]
    with patch("ai_content_studio.publisher.service.httpx.post", side_effect=side_effects), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = svc.publish(publication, "mycode")
    assert result.status == PublicationStatus.PUBLISHED


# --- status transitions ---


def test_publish_returns_published_on_complete(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = svc.publish(publication, "mycode")
    assert result.status == PublicationStatus.PUBLISHED


def test_publish_returns_failed_on_tiktok_failure(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_FAILED_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = svc.publish(publication, "mycode")
    assert result.status == PublicationStatus.FAILED


def test_publish_sets_published_at_on_complete(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = svc.publish(publication, "mycode")
    assert result.published_at is not None
    assert result.published_at.tzinfo is not None


# --- external_id and url mapping ---


def test_publish_maps_external_id(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_COMPLETE_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = svc.publish(publication, "mycode")
    assert result.external_id == "7391234567890"


def test_publish_external_id_none_when_not_in_response(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    body = {
        "data": {"status": "PUBLISH_COMPLETE"},
        "error": {"code": "ok", "message": "", "log_id": "x"},
    }
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(body)), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = svc.publish(publication, "mycode")
    assert result.external_id is None


# --- timeout ---


def test_publish_raises_on_timeout(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = PublicationService(
        oauth=mock_oauth,
        publisher=mock_publisher,
        poll_interval=0.0,
        poll_timeout=0.0,
    )
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_ok(_PROCESSING_BODY)), \
         patch("ai_content_studio.publisher.service.time.sleep"), \
         pytest.raises(PublisherError, match="timed out"):
        svc.publish(publication, "mycode")


# --- exception propagation ---


def test_oauth_error_propagates(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    mock_oauth.exchange_code.side_effect = PublisherError("OAuth failed")
    svc = _make_service(mock_oauth, mock_publisher)
    with pytest.raises(PublisherError, match="OAuth failed"):
        svc.publish(publication, "mycode")


def test_publisher_error_propagates(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    mock_publisher.publish.side_effect = PublisherError("Upload failed")
    svc = _make_service(mock_oauth, mock_publisher)
    with pytest.raises(PublisherError, match="Upload failed"):
        svc.publish(publication, "mycode")


def test_status_fetch_http_error_propagates(
    mock_oauth: MagicMock, mock_publisher: MagicMock, publication: Publication
) -> None:
    svc = _make_service(mock_oauth, mock_publisher)
    with patch("ai_content_studio.publisher.service.httpx.post", return_value=_http_error()), \
         pytest.raises(PublisherError, match="TikTok status fetch failed"):
        svc.publish(publication, "mycode")
