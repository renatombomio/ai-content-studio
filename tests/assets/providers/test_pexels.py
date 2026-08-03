"""Tests for PexelsProvider."""

from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.assets.providers.pexels import PexelsProvider, _best_video_url
from ai_content_studio.core.exceptions import AssetError

_FAKE_PHOTO = {
    "id": 2014422,
    "width": 3024,
    "height": 3024,
    "photographer": "Jane Smith",
    "src": {
        "original": "https://images.pexels.com/photos/2014422/original.jpg",
        "medium": "https://images.pexels.com/photos/2014422/medium.jpg",
    },
}

_FAKE_VIDEO = {
    "id": 1448735,
    "width": 1920,
    "height": 1080,
    "duration": 37,
    "image": "https://images.pexels.com/videos/1448735/preview.jpg",
    "user": {"id": 574687, "name": "John Doe", "url": "https://www.pexels.com/@johndoe"},
    "video_files": [
        {"id": 1, "quality": "sd", "file_type": "video/mp4", "width": 1280, "height": 720, "link": "https://videos.pexels.com/sd.mp4"},
        {"id": 2, "quality": "hd", "file_type": "video/mp4", "width": 1920, "height": 1080, "link": "https://videos.pexels.com/hd.mp4"},
    ],
    "video_pictures": [],
}

_PHOTO_RESPONSE = {"photos": [_FAKE_PHOTO], "total_results": 1}
_VIDEO_RESPONSE = {"videos": [_FAKE_VIDEO], "total_results": 1}
_EMPTY_PHOTO = {"photos": [], "total_results": 0}
_EMPTY_VIDEO = {"videos": [], "total_results": 0}


def _ok(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _error_response() -> MagicMock:
    import httpx
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="HTTP 401", request=MagicMock(), response=MagicMock(status_code=401)
    )
    return resp


# --- Auth ---

def test_search_sends_authorization_header() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        PexelsProvider().search("cocoa farm")
        assert "Authorization" in str(mock_get.call_args_list[0])


# --- Endpoints ---

def test_search_calls_photo_endpoint() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        PexelsProvider().search("cocoa")
        photo_url = mock_get.call_args_list[0].args[0]
        assert "api.pexels.com" in photo_url
        assert "/search" in photo_url


def test_search_calls_video_endpoint() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        PexelsProvider().search("cocoa")
        video_url = mock_get.call_args_list[1].args[0]
        assert "videos/search" in video_url


def test_search_sends_query_param() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_EMPTY_VIDEO)]
        PexelsProvider().search("harvest sunset")
        assert "harvest sunset" in str(mock_get.call_args_list[0])


def test_search_sends_limit_as_per_page() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_EMPTY_VIDEO)]
        PexelsProvider().search("cocoa", limit=7)
        assert "7" in str(mock_get.call_args_list[0])


# --- Photo mapping ---

def test_photo_returns_asset() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        results = PexelsProvider().search("cocoa")
        assert any(a.asset_type == "photo" for a in results)


def test_photo_mapping_provider_id() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.provider_id == "2014422"


def test_photo_mapping_source() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.source == "pexels"


def test_photo_mapping_url_is_original() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.url == "https://images.pexels.com/photos/2014422/original.jpg"


def test_photo_mapping_thumbnail_is_medium() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.thumbnail_url == "https://images.pexels.com/photos/2014422/medium.jpg"


def test_photo_mapping_dimensions() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.width == 3024
        assert asset.height == 3024


def test_photo_mapping_author() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.author == "Jane Smith"


def test_photo_mapping_duration_is_none() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.duration is None


def test_photo_mapping_license() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.license == "Pexels License"


# --- Video mapping ---

def test_video_returns_asset() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        results = PexelsProvider().search("cocoa")
        assert any(a.asset_type == "video" for a in results)


def test_video_mapping_provider_id() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "video")
        assert asset.provider_id == "1448735"


def test_video_mapping_selects_hd_mp4() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "video")
        assert asset.url == "https://videos.pexels.com/hd.mp4"


def test_video_mapping_thumbnail() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "video")
        assert asset.thumbnail_url == "https://images.pexels.com/videos/1448735/preview.jpg"


def test_video_mapping_duration() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "video")
        assert asset.duration == 37.0


def test_video_mapping_author() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "video")
        assert asset.author == "John Doe"


def test_video_mapping_path_is_none() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PexelsProvider().search("cocoa") if a.asset_type == "video")
        assert asset.path is None


# --- Combined results ---

def test_search_returns_photos_and_videos() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_PHOTO_RESPONSE), _ok(_VIDEO_RESPONSE)]
        results = PexelsProvider().search("cocoa")
        types = {a.asset_type for a in results}
        assert "photo" in types
        assert "video" in types


def test_empty_results_return_empty_list() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_PHOTO), _ok(_EMPTY_VIDEO)]
        assert PexelsProvider().search("cocoa") == []


# --- Errors ---

def test_api_failure_raises_asset_error() -> None:
    import httpx as httpx_module

    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = httpx_module.ConnectError("refused")
        with pytest.raises(AssetError):
            PexelsProvider().search("cocoa")


def test_http_status_error_raises_asset_error() -> None:
    with patch("ai_content_studio.assets.providers.pexels.httpx.get") as mock_get:
        mock_get.side_effect = [_error_response(), _ok(_EMPTY_VIDEO)]
        with pytest.raises(AssetError):
            PexelsProvider().search("cocoa")


# --- _best_video_url ---

def test_best_video_url_prefers_hd() -> None:
    files = [
        {"quality": "sd", "file_type": "video/mp4", "link": "sd.mp4"},
        {"quality": "hd", "file_type": "video/mp4", "link": "hd.mp4"},
    ]
    assert _best_video_url(files) == "hd.mp4"


def test_best_video_url_falls_back_to_sd() -> None:
    files = [{"quality": "sd", "file_type": "video/mp4", "link": "sd.mp4"}]
    assert _best_video_url(files) == "sd.mp4"


def test_best_video_url_empty_returns_empty_string() -> None:
    assert _best_video_url([]) == ""
