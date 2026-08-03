"""Tests for PixabayProvider."""

from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.assets.providers.pixabay import PixabayProvider, _as_float, _as_int
from ai_content_studio.core.exceptions import AssetError

_FAKE_IMAGE = {
    "id": 195893,
    "type": "photo",
    "largeImageURL": "https://pixabay.com/get/blossom_1280.jpg",
    "previewURL": "https://cdn.pixabay.com/photo/blossom_150.jpg",
    "imageWidth": 4000,
    "imageHeight": 2670,
    "user": "photographer_name",
}

_FAKE_VIDEO = {
    "id": 125,
    "type": "film",
    "duration": 60,
    "picture_id": "649485029",
    "videos": {
        "large": {"url": "https://player.vimeo.com/external/large.mp4", "width": 1920, "height": 1080, "size": 272227874},
        "medium": {"url": "https://player.vimeo.com/external/medium.mp4", "width": 1280, "height": 720, "size": 138914940},
    },
    "user": "videographer_name",
}

_IMAGE_RESPONSE = {"total": 1, "totalHits": 1, "hits": [_FAKE_IMAGE]}
_VIDEO_RESPONSE = {"total": 1, "totalHits": 1, "hits": [_FAKE_VIDEO]}
_EMPTY_IMAGE = {"total": 0, "totalHits": 0, "hits": []}
_EMPTY_VIDEO = {"total": 0, "totalHits": 0, "hits": []}


def _ok(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _error() -> MagicMock:
    import httpx
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="HTTP 403", request=MagicMock(), response=MagicMock(status_code=403)
    )
    return resp


# --- Auth ---

def test_search_sends_api_key_as_query_param() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        PixabayProvider().search("cocoa farm")
        assert "key" in str(mock_get.call_args_list[0])


# --- Endpoints ---

def test_search_calls_image_endpoint() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        PixabayProvider().search("cocoa")
        url = mock_get.call_args_list[0].args[0]
        assert "pixabay.com/api/" in url
        assert "videos" not in url


def test_search_calls_video_endpoint() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        PixabayProvider().search("cocoa")
        url = mock_get.call_args_list[1].args[0]
        assert "pixabay.com/api/videos/" in url


def test_search_sends_query_param() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_EMPTY_VIDEO)]
        PixabayProvider().search("golden harvest")
        assert "golden harvest" in str(mock_get.call_args_list[0])


def test_search_sends_limit_as_per_page() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_EMPTY_VIDEO)]
        PixabayProvider().search("cocoa", limit=8)
        assert "8" in str(mock_get.call_args_list[0])


# --- Image mapping ---

def test_image_returns_asset() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        results = PixabayProvider().search("cocoa")
        assert any(a.asset_type == "photo" for a in results)


def test_image_mapping_provider_id() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.provider_id == "195893"


def test_image_mapping_source() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.source == "pixabay"


def test_image_mapping_url_is_large() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.url == "https://pixabay.com/get/blossom_1280.jpg"


def test_image_mapping_thumbnail_is_preview() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.thumbnail_url == "https://cdn.pixabay.com/photo/blossom_150.jpg"


def test_image_mapping_dimensions() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.width == 4000
        assert asset.height == 2670


def test_image_mapping_author() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.author == "photographer_name"


def test_image_mapping_duration_is_none() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.duration is None


def test_image_mapping_license() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.license == "Pixabay Content License"


def test_image_mapping_path_is_none() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_EMPTY_VIDEO)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "photo")
        assert asset.path is None


# --- Video mapping ---

def test_video_returns_asset() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        results = PixabayProvider().search("cocoa")
        assert any(a.asset_type == "video" for a in results)


def test_video_mapping_provider_id() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "video")
        assert asset.provider_id == "125"


def test_video_mapping_url_prefers_large() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "video")
        assert asset.url == "https://player.vimeo.com/external/large.mp4"


def test_video_mapping_thumbnail_uses_vimeo_cdn() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "video")
        assert "649485029" in asset.thumbnail_url
        assert "vimeocdn.com" in asset.thumbnail_url


def test_video_mapping_dimensions() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "video")
        assert asset.width == 1920
        assert asset.height == 1080


def test_video_mapping_duration() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "video")
        assert asset.duration == 60.0


def test_video_mapping_author() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_VIDEO_RESPONSE)]
        asset = next(a for a in PixabayProvider().search("cocoa") if a.asset_type == "video")
        assert asset.author == "videographer_name"


# --- Combined ---

def test_search_returns_images_and_videos() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_IMAGE_RESPONSE), _ok(_VIDEO_RESPONSE)]
        results = PixabayProvider().search("cocoa")
        types = {a.asset_type for a in results}
        assert "photo" in types
        assert "video" in types


def test_empty_results_return_empty_list() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_ok(_EMPTY_IMAGE), _ok(_EMPTY_VIDEO)]
        assert PixabayProvider().search("cocoa") == []


# --- Errors ---

def test_http_error_raises_asset_error() -> None:
    import httpx as httpx_module

    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = httpx_module.ConnectError("refused")
        with pytest.raises(AssetError):
            PixabayProvider().search("cocoa")


def test_http_status_error_raises_asset_error() -> None:
    with patch("ai_content_studio.assets.providers.pixabay.httpx.get") as mock_get:
        mock_get.side_effect = [_error(), _ok(_EMPTY_VIDEO)]
        with pytest.raises(AssetError):
            PixabayProvider().search("cocoa")


# --- Helpers ---

def test_as_int_valid() -> None:
    assert _as_int(1920) == 1920


def test_as_int_none_returns_none() -> None:
    assert _as_int(None) is None


def test_as_float_valid() -> None:
    assert _as_float(60) == 60.0


def test_as_float_none_returns_none() -> None:
    assert _as_float(None) is None
