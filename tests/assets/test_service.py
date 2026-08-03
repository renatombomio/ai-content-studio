"""Tests for AssetService."""

from unittest.mock import MagicMock

import pytest

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.assets.service import AssetService, _deduplicate
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset, Scene
from ai_content_studio.shared.models.emotion import Emotion

# --- Helpers ---

def _make_scene() -> Scene:
    return Scene(
        order=1,
        narration="A farmer walks at dawn.",
        visual_prompt="Misty field at sunrise.",
        emotion=Emotion.HOPE,
        duration_seconds=5.0,
    )


def _make_asset(source: str = "pexels", provider_id: str = "1") -> Asset:
    return Asset(
        scene_id="",
        source=source,
        provider_id=provider_id,
        asset_type="photo",
        url="https://example.com/img.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
    )


def _make_provider(assets: list[Asset] | None = None, fail: bool = False) -> MagicMock:
    provider = MagicMock(spec=AssetProvider)
    if fail:
        provider.search.side_effect = AssetError("provider down")
    else:
        provider.search.return_value = assets or []
    return provider


def _make_service(
    providers: list[MagicMock] | None = None,
    query: str = "hopeful scene",
) -> tuple[AssetService, MagicMock, MagicMock]:
    builder = MagicMock(spec=SearchQueryBuilder)
    builder.build.return_value = query
    ranker = MagicMock(spec=AssetRanker)
    ranker.rank.side_effect = lambda scene, assets: assets
    service = AssetService(
        query_builder=builder,
        providers=providers or [],
        ranker=ranker,
    )
    return service, builder, ranker


# --- Query builder ---

def test_query_builder_called_once() -> None:
    service, builder, _ = _make_service(providers=[_make_provider()])
    service.find_assets(_make_scene())
    builder.build.assert_called_once()


def test_query_builder_receives_scene() -> None:
    scene = _make_scene()
    service, builder, _ = _make_service(providers=[_make_provider()])
    service.find_assets(scene)
    builder.build.assert_called_once_with(scene)


# --- Provider calls ---

def test_all_providers_receive_same_query() -> None:
    p1 = _make_provider()
    p2 = _make_provider()
    service, _, _ = _make_service(providers=[p1, p2], query="lonely person walking")
    service.find_assets(_make_scene())
    p1.search.assert_called_once_with("lonely person walking", limit=10)
    p2.search.assert_called_once_with("lonely person walking", limit=10)


def test_limit_passed_to_providers() -> None:
    provider = _make_provider()
    service, _, _ = _make_service(providers=[provider])
    service.find_assets(_make_scene(), limit=5)
    provider.search.assert_called_once_with(provider.search.call_args.args[0], limit=5)


def test_results_from_all_providers_merged() -> None:
    a1 = _make_asset("pexels", "1")
    a2 = _make_asset("freepik", "2")
    p1 = _make_provider([a1])
    p2 = _make_provider([a2])
    service, _, ranker = _make_service(providers=[p1, p2])
    service.find_assets(_make_scene())
    merged = ranker.rank.call_args.args[1]
    assert a1 in merged
    assert a2 in merged


# --- Deduplication ---

def test_duplicates_removed_by_source_and_provider_id() -> None:
    asset = _make_asset("pexels", "42")
    duplicate = _make_asset("pexels", "42")
    p1 = _make_provider([asset])
    p2 = _make_provider([duplicate])
    service, _, ranker = _make_service(providers=[p1, p2])
    service.find_assets(_make_scene())
    ranked_assets = ranker.rank.call_args.args[1]
    assert len(ranked_assets) == 1


def test_same_provider_id_different_source_not_deduplicated() -> None:
    a1 = _make_asset("pexels", "1")
    a2 = _make_asset("freepik", "1")
    p1 = _make_provider([a1])
    p2 = _make_provider([a2])
    service, _, ranker = _make_service(providers=[p1, p2])
    service.find_assets(_make_scene())
    ranked_assets = ranker.rank.call_args.args[1]
    assert len(ranked_assets) == 2


def test_deduplicate_preserves_first_occurrence() -> None:
    a1 = _make_asset("pexels", "1")
    a2 = _make_asset("pexels", "1")
    result = _deduplicate([a1, a2])
    assert result == [a1]


def test_deduplicate_empty_list() -> None:
    assert _deduplicate([]) == []


# --- Ranking ---

def test_ranker_receives_scene_and_assets() -> None:
    scene = _make_scene()
    asset = _make_asset()
    provider = _make_provider([asset])
    service, _, ranker = _make_service(providers=[provider])
    service.find_assets(scene)
    ranker.rank.assert_called_once()
    call_scene, call_assets = ranker.rank.call_args.args
    assert call_scene is scene
    assert asset in call_assets


def test_ranker_output_is_returned() -> None:
    asset = _make_asset()
    provider = _make_provider([asset])
    service, _, ranker = _make_service(providers=[provider])
    ranked = [asset]
    ranker.rank.side_effect = None
    ranker.rank.return_value = ranked
    result = service.find_assets(_make_scene())
    assert result is ranked


# --- Provider failure handling ---

def test_one_provider_failure_continues() -> None:
    good_asset = _make_asset("pexels", "1")
    failing = _make_provider(fail=True)
    working = _make_provider([good_asset])
    service, _, ranker = _make_service(providers=[failing, working])
    service.find_assets(_make_scene())
    ranked_assets = ranker.rank.call_args.args[1]
    assert good_asset in ranked_assets


def test_all_providers_failing_raises_asset_error() -> None:
    p1 = _make_provider(fail=True)
    p2 = _make_provider(fail=True)
    service, _, _ = _make_service(providers=[p1, p2])
    with pytest.raises(AssetError):
        service.find_assets(_make_scene())


def test_no_providers_raises_asset_error() -> None:
    service, _, _ = _make_service(providers=[])
    with pytest.raises(AssetError):
        service.find_assets(_make_scene())
