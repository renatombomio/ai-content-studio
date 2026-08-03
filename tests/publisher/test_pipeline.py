"""End-to-end pipeline test: real objects, mocked HTTP."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.publisher.service import PublicationService
from ai_content_studio.publisher.tiktok import TikTokPublisher
from ai_content_studio.publisher.tiktok_oauth import TikTokOAuth
from ai_content_studio.shared.models import Publication, PublicationStatus

_TOKEN_BODY = {
    "access_token": "act-pipeline",
    "refresh_token": "rft-pipeline",
    "expires_in": 86400,
    "open_id": "uid-1",
}

_CREATOR_INFO_BODY = {
    "data": {
        "privacy_level_options": ["PUBLIC_TO_EVERYONE"],
        "comment_disabled": False,
        "duet_disabled": False,
        "stitch_disabled": False,
        "max_video_post_duration_sec": 600,
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}

_INIT_BODY = {
    "data": {
        "publish_id": "pub-pipeline-001",
        "upload_url": "https://upload.tiktok.com/v1/pipeline?key=abc",
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}

_STATUS_BODY = {
    "data": {
        "status": "PUBLISH_COMPLETE",
        "publicaly_available_post_id": "9999999999",
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}


@pytest.fixture
def video_file(tmp_path: Path) -> Path:
    path = tmp_path / "cocoa.mp4"
    path.write_bytes(b"x" * 50)
    return path


@pytest.fixture
def publication(video_file: Path) -> Publication:
    return Publication(
        platform="tiktok",
        video_path=video_file,
        title="The Origin of Cocoa",
        caption="Did you know chocolate has a 3,000-year history?",
        hashtags=["#CocoaTalk", "#Chocolate"],
    )


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


def test_full_pipeline_publishes_successfully(publication: Publication) -> None:
    oauth = TikTokOAuth()
    publisher = TikTokPublisher(oauth=oauth)
    service = PublicationService(
        oauth=oauth,
        publisher=publisher,
        poll_interval=0.0,
        poll_timeout=30.0,
    )

    # httpx.post is a single global — patch once with all calls in sequence:
    # 1. tiktok_oauth: token exchange
    # 2. tiktok: creator_info
    # 3. tiktok: video/init
    # 4. service: status/fetch
    post_effects = [
        _ok(_TOKEN_BODY),
        _ok(_CREATOR_INFO_BODY),
        _ok(_INIT_BODY),
        _ok(_STATUS_BODY),
    ]

    with patch("httpx.post", side_effect=post_effects), \
         patch("httpx.put", return_value=_upload_ok()), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = service.publish(publication, "authcode-abc")

    assert result.status == PublicationStatus.PUBLISHED
    assert result.publish_id == "pub-pipeline-001"
    assert result.external_id == "9999999999"
    assert result.published_at is not None


def test_full_pipeline_fails_on_tiktok_rejection(publication: Publication) -> None:
    oauth = TikTokOAuth()
    publisher = TikTokPublisher(oauth=oauth)
    service = PublicationService(
        oauth=oauth,
        publisher=publisher,
        poll_interval=0.0,
        poll_timeout=30.0,
    )

    failed_status = {
        "data": {"status": "FAILED", "fail_reason": "content_violation"},
        "error": {"code": "ok", "message": "", "log_id": "x"},
    }
    post_effects = [_ok(_TOKEN_BODY), _ok(_CREATOR_INFO_BODY), _ok(_INIT_BODY), _ok(failed_status)]

    with patch("httpx.post", side_effect=post_effects), \
         patch("httpx.put", return_value=_upload_ok()), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = service.publish(publication, "authcode-abc")

    assert result.status == PublicationStatus.FAILED


def test_full_pipeline_status_progression(publication: Publication) -> None:
    oauth = TikTokOAuth()
    publisher = TikTokPublisher(oauth=oauth)
    service = PublicationService(
        oauth=oauth,
        publisher=publisher,
        poll_interval=0.0,
        poll_timeout=30.0,
    )

    processing = {
        "data": {"status": "PROCESSING_UPLOAD"},
        "error": {"code": "ok", "message": "", "log_id": "x"},
    }
    # token + creator_info + init + processing + processing + complete
    post_effects = [
        _ok(_TOKEN_BODY),
        _ok(_CREATOR_INFO_BODY),
        _ok(_INIT_BODY),
        _ok(processing),
        _ok(processing),
        _ok(_STATUS_BODY),
    ]

    with patch("httpx.post", side_effect=post_effects), \
         patch("httpx.put", return_value=_upload_ok()), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = service.publish(publication, "authcode-abc")

    assert result.status == PublicationStatus.PUBLISHED
