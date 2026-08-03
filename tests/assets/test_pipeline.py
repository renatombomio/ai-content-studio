"""End-to-end Asset Engine pipeline test using fake providers."""

import pytest

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.assets.service import AssetService
from ai_content_studio.core.exceptions import AssetError
from ai_content_studio.shared.models import Asset, Scene
from ai_content_studio.shared.models.emotion import Emotion

# --- Fake providers ---

def _make_asset(source: str, provider_id: str, asset_type: str = "photo", **kwargs: object) -> Asset:
    return Asset(
        scene_id="",
        source=source,
        provider_id=provider_id,
        asset_type=asset_type,
        url=f"https://{source}.com/{provider_id}.jpg",
        thumbnail_url=f"https://{source}.com/{provider_id}_thumb.jpg",
        **kwargs,  # type: ignore[arg-type]
    )


class FakeFreepikProvider(AssetProvider):
    """Returns fixed Freepik assets."""

    def __init__(self, assets: list[Asset] | None = None) -> None:
        self.received_query: str | None = None
        self._assets = assets if assets is not None else [
            _make_asset("freepik", "101", asset_type="photo", width=740, height=640),
            _make_asset("freepik", "102", asset_type="vector", width=800, height=600),
        ]

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        self.received_query = query
        return self._assets[:limit]


class FakePexelsProvider(AssetProvider):
    """Returns fixed Pexels assets."""

    def __init__(self, assets: list[Asset] | None = None) -> None:
        self.received_query: str | None = None
        self._assets = assets if assets is not None else [
            _make_asset("pexels", "201", asset_type="photo", width=3024, height=3024),
            _make_asset("pexels", "202", asset_type="video", width=1920, height=1080, duration=37.0),
        ]

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        self.received_query = query
        return self._assets[:limit]


class FakePixabayProvider(AssetProvider):
    """Returns fixed Pixabay assets."""

    def __init__(self, assets: list[Asset] | None = None) -> None:
        self.received_query: str | None = None
        self._assets = assets if assets is not None else [
            _make_asset("pixabay", "301", asset_type="photo", width=4000, height=2670),
            _make_asset("pixabay", "302", asset_type="video", width=1920, height=1080, duration=60.0),
        ]

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        self.received_query = query
        return self._assets[:limit]


class FailingProvider(AssetProvider):
    """Always raises AssetError."""

    def search(self, query: str, limit: int = 10) -> list[Asset]:
        raise AssetError("provider unavailable")


# --- Pipeline fixture ---

def _make_scene(emotion: Emotion = Emotion.HOPE, duration_seconds: float = 5.0) -> Scene:
    return Scene(
        order=1,
        narration="A farmer plants a seed at dawn.",
        visual_prompt="Hands pressing seed into rich soil.",
        emotion=emotion,
        duration_seconds=duration_seconds,
    )


def _make_pipeline(
    providers: list[AssetProvider] | None = None,
) -> tuple[AssetService, FakeFreepikProvider, FakePexelsProvider, FakePixabayProvider]:
    freepik = FakeFreepikProvider()
    pexels = FakePexelsProvider()
    pixabay = FakePixabayProvider()
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=providers if providers is not None else [freepik, pexels, pixabay],
        ranker=AssetRanker(),
    )
    return service, freepik, pexels, pixabay


# --- Query builder integration ---

def test_pipeline_builds_query_from_scene() -> None:
    service, freepik, _, _ = _make_pipeline()
    service.find_assets(_make_scene())
    assert freepik.received_query is not None
    assert len(freepik.received_query) > 0


def test_pipeline_all_providers_receive_same_query() -> None:
    service, freepik, pexels, pixabay = _make_pipeline()
    service.find_assets(_make_scene())
    assert freepik.received_query == pexels.received_query == pixabay.received_query


def test_pipeline_query_reflects_scene_emotion() -> None:
    service, freepik, _, _ = _make_pipeline()
    service.find_assets(_make_scene(emotion=Emotion.GRIEF))
    assert freepik.received_query is not None
    # Grief maps to "grieving" — confirm emotion influences query
    assert "grieving" in freepik.received_query


# --- Result merging ---

def test_pipeline_merges_all_provider_results() -> None:
    service, _, _, _ = _make_pipeline()
    results = service.find_assets(_make_scene())
    sources = {a.source for a in results}
    assert "freepik" in sources
    assert "pexels" in sources
    assert "pixabay" in sources


def test_pipeline_returns_list_of_assets() -> None:
    service, _, _, _ = _make_pipeline()
    results = service.find_assets(_make_scene())
    assert isinstance(results, list)
    assert all(isinstance(a, Asset) for a in results)


# --- Deduplication ---

def test_pipeline_removes_duplicates() -> None:
    duplicate = _make_asset("pexels", "999", asset_type="photo")
    freepik = FakeFreepikProvider(assets=[_make_asset("freepik", "1")])
    pexels = FakePexelsProvider(assets=[duplicate])
    pixabay = FakePixabayProvider(assets=[duplicate])  # same source+id as pexels
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[freepik, pexels, pixabay],
        ranker=AssetRanker(),
    )
    results = service.find_assets(_make_scene())
    pexels_assets = [a for a in results if a.source == "pexels"]
    assert len(pexels_assets) == 1


def test_pipeline_same_id_different_source_kept() -> None:
    freepik = FakeFreepikProvider(assets=[_make_asset("freepik", "1")])
    pexels = FakePexelsProvider(assets=[_make_asset("pexels", "1")])
    pixabay = FakePixabayProvider(assets=[])
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[freepik, pexels, pixabay],
        ranker=AssetRanker(),
    )
    results = service.find_assets(_make_scene())
    assert len(results) == 2


# --- Ranking ---

def test_pipeline_returns_assets_in_ranked_order() -> None:
    # Portrait video close to scene duration should score highest
    portrait_video = _make_asset(
        "pexels", "top", asset_type="video", width=1080, height=1920, duration=5.0
    )
    landscape_photo = _make_asset(
        "pixabay", "low", asset_type="photo", width=640, height=480
    )
    freepik = FakeFreepikProvider(assets=[])
    pexels = FakePexelsProvider(assets=[landscape_photo])
    pixabay = FakePixabayProvider(assets=[portrait_video])
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[freepik, pexels, pixabay],
        ranker=AssetRanker(),
    )
    results = service.find_assets(_make_scene(emotion=Emotion.HOPE, duration_seconds=5.0))
    assert results[0].provider_id == "top"


def test_pipeline_ranking_is_deterministic() -> None:
    service, _, _, _ = _make_pipeline()
    scene = _make_scene()
    assert service.find_assets(scene) == service.find_assets(scene)


# --- Error handling ---

def test_pipeline_one_provider_failing_continues() -> None:
    freepik = FakeFreepikProvider(assets=[_make_asset("freepik", "1")])
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[FailingProvider(), freepik, FailingProvider()],
        ranker=AssetRanker(),
    )
    results = service.find_assets(_make_scene())
    assert any(a.source == "freepik" for a in results)


def test_pipeline_two_providers_failing_still_works() -> None:
    pexels = FakePexelsProvider(assets=[_make_asset("pexels", "1")])
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[FailingProvider(), pexels, FailingProvider()],
        ranker=AssetRanker(),
    )
    results = service.find_assets(_make_scene())
    assert len(results) == 1


def test_pipeline_all_providers_failing_raises_asset_error() -> None:
    service = AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[FailingProvider(), FailingProvider(), FailingProvider()],
        ranker=AssetRanker(),
    )
    with pytest.raises(AssetError):
        service.find_assets(_make_scene())
