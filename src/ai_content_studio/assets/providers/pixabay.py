# Official docs: https://pixabay.com/api/docs/
# Base URL (images): https://pixabay.com/api/
# Base URL (videos): https://pixabay.com/api/videos/
# Authentication: API key passed as query parameter `key`

import httpx

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset

_IMAGE_URL = "https://pixabay.com/api/"
_VIDEO_URL = "https://pixabay.com/api/videos/"
_SOURCE = "pixabay"
_LICENSE = "Pixabay Content License"
_VIMEO_THUMB = "https://i.vimeocdn.com/video/{picture_id}_640x360.jpg"


class PixabayProvider(AssetProvider):
    """Asset provider backed by the Pixabay API (images and videos)."""

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        """Search Pixabay images and videos matching a visual query."""
        settings = get_settings()
        key = settings.pixabay_api_key or ""
        params: dict[str, str | int] = {"key": key, "q": query, "per_page": limit, "safesearch": "true"}

        assets: list[Asset] = []
        try:
            image_resp = httpx.get(_IMAGE_URL, params=params, timeout=10.0)
            image_resp.raise_for_status()
            assets.extend(_map_image(hit) for hit in image_resp.json().get("hits", []))

            video_resp = httpx.get(_VIDEO_URL, params=params, timeout=10.0)
            video_resp.raise_for_status()
            assets.extend(_map_video(hit) for hit in video_resp.json().get("hits", []))
        except httpx.HTTPError as exc:
            raise AssetError(f"Pixabay API error: {exc}") from exc

        return assets


def _map_image(hit: dict[str, object]) -> Asset:
    return Asset(
        scene_id="",
        source=_SOURCE,
        provider_id=str(hit["id"]),
        asset_type=str(hit.get("type", "photo")),
        url=str(hit.get("largeImageURL", hit.get("webformatURL", ""))),
        thumbnail_url=str(hit.get("previewURL", "")),
        width=_as_int(hit.get("imageWidth")),
        height=_as_int(hit.get("imageHeight")),
        duration=None,
        author=str(hit["user"]) if hit.get("user") is not None else None,
        license=_LICENSE,
    )


def _map_video(hit: dict[str, object]) -> Asset:
    videos = hit.get("videos") or {}
    assert isinstance(videos, dict)
    large = videos.get("large") or videos.get("medium") or {}
    assert isinstance(large, dict)

    picture_id = str(hit.get("picture_id", ""))
    thumbnail = _VIMEO_THUMB.format(picture_id=picture_id) if picture_id else ""

    return Asset(
        scene_id="",
        source=_SOURCE,
        provider_id=str(hit["id"]),
        asset_type="video",
        url=str(large.get("url", "")),
        thumbnail_url=thumbnail,
        width=_as_int(large.get("width")),
        height=_as_int(large.get("height")),
        duration=_as_float(hit.get("duration")),
        author=str(hit["user"]) if hit.get("user") is not None else None,
        license=_LICENSE,
    )


def _as_int(val: object) -> int | None:
    return int(val) if isinstance(val, (int, float)) else None


def _as_float(val: object) -> float | None:
    return float(val) if isinstance(val, (int, float)) else None
