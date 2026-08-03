# Official docs: https://www.pexels.com/api/documentation/
# Base URL: https://api.pexels.com/v1
# Endpoints: GET /v1/search (photos), GET /v1/videos/search (videos)
# Authentication: Authorization header (API key, no prefix)

import httpx

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset

_BASE_URL = "https://api.pexels.com/v1"
_PHOTO_PATH = "/search"
_VIDEO_PATH = "/videos/search"
_SOURCE = "pexels"
_LICENSE = "Pexels License"


class PexelsProvider(AssetProvider):
    """Asset provider backed by the Pexels API (photos and videos)."""

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        """Search Pexels photos and videos matching a visual query."""
        settings = get_settings()
        headers = {"Authorization": settings.pexels_api_key or ""}
        params: dict[str, str | int] = {"query": query, "per_page": limit}

        assets: list[Asset] = []
        try:
            photo_resp = httpx.get(
                f"{_BASE_URL}{_PHOTO_PATH}",
                headers=headers,
                params=params,
                timeout=10.0,
            )
            photo_resp.raise_for_status()
            assets.extend(_map_photo(p) for p in photo_resp.json().get("photos", []))

            video_resp = httpx.get(
                f"{_BASE_URL}{_VIDEO_PATH}",
                headers=headers,
                params=params,
                timeout=10.0,
            )
            video_resp.raise_for_status()
            assets.extend(_map_video(v) for v in video_resp.json().get("videos", []))
        except httpx.HTTPError as exc:
            raise AssetError(f"Pexels API error: {exc}") from exc

        return assets


def _as_int(val: object) -> int | None:
    return int(val) if isinstance(val, (int, float)) else None


def _as_float(val: object) -> float | None:
    return float(val) if isinstance(val, (int, float)) else None


def _map_photo(photo: dict[str, object]) -> Asset:
    src = photo.get("src") or {}
    assert isinstance(src, dict)
    return Asset(
        scene_id="",
        source=_SOURCE,
        provider_id=str(photo["id"]),
        asset_type="photo",
        url=str(src.get("original", "")),
        thumbnail_url=str(src.get("medium", "")),
        width=_as_int(photo.get("width")),
        height=_as_int(photo.get("height")),
        duration=None,
        author=str(photo["photographer"]) if photo.get("photographer") is not None else None,
        license=_LICENSE,
    )


def _map_video(video: dict[str, object]) -> Asset:
    video_files = video.get("video_files") or []
    assert isinstance(video_files, list)
    user = video.get("user") or {}
    assert isinstance(user, dict)
    return Asset(
        scene_id="",
        source=_SOURCE,
        provider_id=str(video["id"]),
        asset_type="video",
        url=_best_video_url(video_files),
        thumbnail_url=str(video.get("image", "")),
        width=_as_int(video.get("width")),
        height=_as_int(video.get("height")),
        duration=_as_float(video.get("duration")),
        author=str(user["name"]) if user.get("name") is not None else None,
        license=_LICENSE,
    )


def _best_video_url(video_files: list[object]) -> str:
    """Select the highest quality MP4 link. Prefers HD, falls back to SD."""
    dicts = [f for f in video_files if isinstance(f, dict)]
    mp4 = [f for f in dicts if f.get("file_type") == "video/mp4"]
    hd = [f for f in mp4 if f.get("quality") == "hd"]
    chosen = hd[0] if hd else (mp4[0] if mp4 else (dicts[0] if dicts else {}))
    return str(chosen.get("link", ""))
