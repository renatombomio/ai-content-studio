"""Tests for TikTokPublisher."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from ai_content_studio.core.exceptions import PublisherError
from ai_content_studio.publisher.auth import OAuthToken
from ai_content_studio.publisher.tiktok import _CREATOR_INFO_URL, _VIDEO_INIT_URL, TikTokPublisher
from ai_content_studio.shared.models import Publication, PublicationStatus

_CREATOR_INFO_BODY = {
    "data": {
        "privacy_level_options": ["PUBLIC_TO_EVERYONE", "SELF_ONLY"],
        "comment_disabled": False,
        "duet_disabled": False,
        "stitch_disabled": False,
        "max_video_post_duration_sec": 600,
    },
    "error": {"code": "ok", "message": "", "log_id": "log1"},
}

_VIDEO_INIT_BODY = {
    "data": {
        "publish_id": "pub-abc123",
        "upload_url": "https://upload.tiktok.com/v1/abc?key=xyz",
    },
    "error": {"code": "ok", "message": "", "log_id": "log2"},
}


@pytest.fixture
def video_file(tmp_path: Path) -> Path:
    path = tmp_path / "video.mp4"
    path.write_bytes(b"x" * 50)
    return path


@pytest.fixture
def token() -> OAuthToken:
    return OAuthToken(
        access_token="act-abc123",
        refresh_token="rft-xyz",
        expires_at=datetime(2026, 8, 4, 10, 0, tzinfo=UTC),
    )


@pytest.fixture
def publication(video_file: Path) -> Publication:
    return Publication(
        platform="tiktok",
        video_path=video_file,
        title="The Origin of Cocoa",
        caption="Did you know?",
        hashtags=["#CocoaTalk", "#Chocolate"],
    )


@pytest.fixture
def publisher() -> TikTokPublisher:
    return TikTokPublisher(oauth=MagicMock())


def _ok(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _upload_ok() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 201
    resp.raise_for_status = MagicMock()
    return resp


def _http_error() -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="HTTP 500", request=MagicMock(), response=MagicMock(status_code=500)
    )
    return resp


def _post_sides() -> list[MagicMock]:
    return [_ok(_CREATOR_INFO_BODY), _ok(_VIDEO_INIT_BODY)]


# --- creator_info ---


def test_publish_requests_creator_info(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()) as mock_post, \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        publisher.publish(publication, token)
    first_call = mock_post.call_args_list[0]
    assert first_call.args[0] == _CREATOR_INFO_URL


def test_publish_sends_bearer_token_to_creator_info(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()) as mock_post, \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        publisher.publish(publication, token)
    headers = mock_post.call_args_list[0].kwargs["headers"]
    assert headers["Authorization"] == f"Bearer {token.access_token}"


# --- upload initialization ---


def test_publish_initializes_upload(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()) as mock_post, \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        publisher.publish(publication, token)
    second_call = mock_post.call_args_list[1]
    assert second_call.args[0] == _VIDEO_INIT_URL


def test_publish_init_payload_contains_source_info(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()) as mock_post, \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        publisher.publish(publication, token)
    payload = mock_post.call_args_list[1].kwargs["json"]
    assert payload["source_info"]["source"] == "FILE_UPLOAD"
    assert payload["source_info"]["video_size"] == 50


def test_publish_init_payload_embeds_hashtags_in_title(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()) as mock_post, \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        publisher.publish(publication, token)
    post_info = mock_post.call_args_list[1].kwargs["json"]["post_info"]
    assert "#CocoaTalk" in post_info["title"]
    assert "#Chocolate" in post_info["title"]


def test_publish_init_uses_privacy_from_creator_info(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()) as mock_post, \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        publisher.publish(publication, token)
    post_info = mock_post.call_args_list[1].kwargs["json"]["post_info"]
    assert post_info["privacy_level"] == "PUBLIC_TO_EVERYONE"


# --- video upload ---


def test_publish_uploads_video(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()), \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()) as mock_put:
        publisher.publish(publication, token)
    mock_put.assert_called_once()
    call_url = mock_put.call_args.args[0]
    assert call_url == _VIDEO_INIT_BODY["data"]["upload_url"]


def test_publish_upload_sets_content_range_header(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()), \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()) as mock_put:
        publisher.publish(publication, token)
    headers = mock_put.call_args.kwargs["headers"]
    assert headers["Content-Range"] == "bytes 0-49/50"


# --- publish_id and status ---


def test_publish_id_mapped(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()), \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        result = publisher.publish(publication, token)
    assert result.publish_id == "pub-abc123"


def test_publish_status_set_to_processing(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()), \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        result = publisher.publish(publication, token)
    assert result.status == PublicationStatus.PROCESSING


def test_publish_returns_publication_instance(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()), \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_upload_ok()):
        result = publisher.publish(publication, token)
    assert isinstance(result, Publication)


# --- validation ---


def test_raises_publisher_error_on_missing_video_file(
    publisher: TikTokPublisher, token: OAuthToken, tmp_path: Path
) -> None:
    pub = Publication(
        platform="tiktok",
        video_path=tmp_path / "missing.mp4",
        title="T",
        caption="C",
        hashtags=[],
    )
    with pytest.raises(PublisherError, match="Video file not found"):
        publisher.publish(pub, token)


# --- API failures ---


def test_raises_publisher_error_on_creator_info_failure(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", return_value=_http_error()), \
         pytest.raises(PublisherError, match="TikTok API request failed"):
        publisher.publish(publication, token)


def test_raises_publisher_error_on_init_failure(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=[_ok(_CREATOR_INFO_BODY), _http_error()]), \
         pytest.raises(PublisherError, match="TikTok API request failed"):
        publisher.publish(publication, token)


def test_raises_publisher_error_on_upload_failure(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    with patch("ai_content_studio.publisher.tiktok.httpx.post", side_effect=_post_sides()), \
         patch("ai_content_studio.publisher.tiktok.httpx.put", return_value=_http_error()), \
         pytest.raises(PublisherError, match="TikTok video upload failed"):
        publisher.publish(publication, token)


def test_raises_publisher_error_on_api_error_body(
    publisher: TikTokPublisher, publication: Publication, token: OAuthToken
) -> None:
    error_body = {
        "data": {},
        "error": {"code": "access_token_invalid", "message": "Token expired", "log_id": "x"},
    }
    with patch("ai_content_studio.publisher.tiktok.httpx.post", return_value=_ok(error_body)), \
         pytest.raises(PublisherError, match="TikTok API error"):
        publisher.publish(publication, token)
