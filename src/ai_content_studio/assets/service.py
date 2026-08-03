"""Asset service — orchestrates the full asset sourcing pipeline for a scene."""

import logging

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset, Scene

logger = logging.getLogger(__name__)


class AssetService:
    """Orchestrates query building, provider calls, deduplication, and ranking."""

    def __init__(
        self,
        query_builder: SearchQueryBuilder,
        providers: list[AssetProvider],
        ranker: AssetRanker,
    ) -> None:
        self._query_builder = query_builder
        self._providers = providers
        self._ranker = ranker

    def find_assets(self, scene: Scene, limit: int = 10) -> list[Asset]:
        """Build a query, search all providers, deduplicate, rank, and return assets."""
        query = self._query_builder.build(scene)

        raw: list[Asset] = []
        failed = 0
        for provider in self._providers:
            try:
                raw.extend(provider.search(query, limit=limit))
            except AssetError as exc:
                failed += 1
                logger.warning("Provider %s failed: %s", type(provider).__name__, exc)

        if failed == len(self._providers):
            raise AssetError("All asset providers failed.")

        unique = _deduplicate(raw)
        return self._ranker.rank(scene, unique)


def _deduplicate(assets: list[Asset]) -> list[Asset]:
    seen: set[tuple[str, str]] = set()
    result: list[Asset] = []
    for asset in assets:
        key = (asset.source, asset.provider_id)
        if key not in seen:
            seen.add(key)
            result.append(asset)
    return result
