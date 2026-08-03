"""Tests for AssetProvider interface."""

import pytest

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.shared.models import Asset


def test_asset_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        AssetProvider()  # type: ignore[abstract]


def test_search_must_be_implemented() -> None:
    class IncompleteProvider(AssetProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()  # type: ignore[abstract]


def test_concrete_provider_is_instantiable() -> None:
    class ConcreteProvider(AssetProvider):
        def search(self, query: str, limit: int = 10) -> list[Asset]:
            return []

    provider = ConcreteProvider()
    assert isinstance(provider, AssetProvider)


def test_search_returns_list() -> None:
    class ConcreteProvider(AssetProvider):
        def search(self, query: str, limit: int = 10) -> list[Asset]:
            return []

    provider = ConcreteProvider()
    result = provider.search("cacao farm at sunset")
    assert isinstance(result, list)


def test_search_default_limit_is_ten() -> None:
    received: dict[str, int] = {}

    class ConcreteProvider(AssetProvider):
        def search(self, query: str, limit: int = 10) -> list[Asset]:
            received["limit"] = limit
            return []

    ConcreteProvider().search("query")
    assert received["limit"] == 10
