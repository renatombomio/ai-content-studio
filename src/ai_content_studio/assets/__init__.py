"""Assets module — visual asset sourcing."""

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.assets.providers.freepik import FreepikProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder

__all__ = ["AssetProvider", "FreepikProvider", "SearchQueryBuilder"]
