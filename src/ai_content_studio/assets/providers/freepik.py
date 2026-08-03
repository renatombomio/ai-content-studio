# Official docs: https://docs.magnific.com/api-reference/resources/get-all-resources
# Base URL: https://api.magnific.com
# Search endpoint: GET /v1/resources

import httpx

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset

_BASE_URL = "https://api.magnific.com"
_SEARCH_PATH = "/v1/resources"
_SOURCE = "freepik"


class FreepikProvider(AssetProvider):
    """Asset provider backed by the Magnific (Freepik) API."""

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        """Search Freepik for assets matching a visual query."""
        settings = get_settings()
        headers = {
            "x-magnific-api-key": settings.freepik_api_key or "",
            "Accept-Language": "en-US",
        }
        params: dict[str, str | int] = {"term": query, "limit": limit}
        try:
            response = httpx.get(
                f"{_BASE_URL}{_SEARCH_PATH}",
                headers=headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AssetError(f"Freepik API error: {exc}") from exc

        return [_map_resource(item) for item in response.json().get("data", [])]


def _map_resource(item: dict[str, object]) -> Asset:
    image = item.get("image") or {}
    assert isinstance(image, dict)
    source = image.get("source") or {}
    assert isinstance(source, dict)

    preview_url = str(source.get("url", ""))
    width, height = _parse_size(str(source.get("size", "")))

    licenses = item.get("licenses") or []
    assert isinstance(licenses, list)
    first = licenses[0]
    license_type = str(first.get("type")) if isinstance(first, dict) else None

    author_data = item.get("author") or {}
    assert isinstance(author_data, dict)
    author_name = author_data.get("name")

    return Asset(
        scene_id="",
        source=_SOURCE,
        provider_id=str(item["id"]),
        asset_type=str(image.get("type", "photo")),
        url=preview_url,
        thumbnail_url=preview_url,
        width=width,
        height=height,
        duration=None,
        author=str(author_name) if author_name is not None else None,
        license=license_type,
    )


def _parse_size(size_str: str) -> tuple[int | None, int | None]:
    if not size_str or "x" not in size_str:
        return None, None
    parts = size_str.split("x", 1)
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None
