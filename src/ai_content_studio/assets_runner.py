"""B-002 — Real Asset Engine bring-up.

Loads output/story.json, searches all providers for each scene,
downloads the best-ranked asset to output/assets/scene_NN.{ext}.
"""

import json
import sys
from pathlib import Path

import httpx

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.assets.providers.freepik import FreepikProvider
from ai_content_studio.assets.providers.pexels import PexelsProvider
from ai_content_studio.assets.providers.pixabay import PixabayProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker, _total_score
from ai_content_studio.assets.service import AssetService
from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Story

_STORY_PATH = Path("output/story.json")
_OUTPUT_DIR = Path("output/assets")

_EXT: dict[str, str] = {
    "video": ".mp4",
    "photo": ".jpg",
    "illustration": ".jpg",
    "vector": ".svg",
}


def main() -> None:
    settings = get_settings()

    providers: list[AssetProvider] = []
    if settings.freepik_api_key:
        providers.append(FreepikProvider())
    if settings.pexels_api_key:
        providers.append(PexelsProvider())
    if settings.pixabay_api_key:
        providers.append(PixabayProvider())

    if not providers:
        print("ERROR: no asset provider API keys configured in .env")
        sys.exit(1)

    print(f"Providers: {[type(p).__name__ for p in providers]}\n")

    story = Story.model_validate(json.loads(_STORY_PATH.read_text()))
    service = AssetService(SearchQueryBuilder(), providers, AssetRanker())

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for scene in sorted(story.scenes, key=lambda s: s.order):
        query = SearchQueryBuilder().build(scene)
        print(f"Scene {scene.order:02d} | emotion={scene.emotion.value} | query='{query}'")

        try:
            ranked = service.find_assets(scene, limit=5)
        except AssetError as exc:
            print(f"  ERROR: {exc}\n")
            continue

        if not ranked:
            print("  No assets found.\n")
            continue

        best = ranked[0]
        score = _total_score(scene, best)
        ext = _EXT.get(best.asset_type, ".bin")
        dest = _OUTPUT_DIR / f"scene_{scene.order:02d}{ext}"

        print(f"  Best: [{best.source}] {best.asset_type} | score={score:.1f} | {best.url[:80]}")

        if not best.url:
            print("  SKIP: empty URL\n")
            continue

        try:
            resp = httpx.get(best.url, timeout=30.0, follow_redirects=True)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            print(f"  Saved: {dest} ({len(resp.content) // 1024} KB)\n")
        except httpx.HTTPError as exc:
            print(f"  DOWNLOAD ERROR: {exc}\n")


if __name__ == "__main__":
    main()
