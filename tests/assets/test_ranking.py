"""Tests for AssetRanker."""

from ai_content_studio.assets.ranking import (
    AssetRanker,
    _score_asset_type,
    _score_duration,
    _score_emotion,
    _score_orientation,
    _score_resolution,
)
from ai_content_studio.shared.models import Asset, Scene
from ai_content_studio.shared.models.emotion import Emotion

# --- Helpers ---

def _make_scene(
    emotion: Emotion = Emotion.LONELINESS,
    duration_seconds: float = 5.0,
) -> Scene:
    return Scene(
        order=1,
        narration="A person stands alone.",
        visual_prompt="Empty street at dusk.",
        emotion=emotion,
        duration_seconds=duration_seconds,
    )


def _make_asset(
    asset_type: str = "photo",
    width: int | None = 1080,
    height: int | None = 1920,
    duration: float | None = None,
    source: str = "pexels",
) -> Asset:
    return Asset(
        scene_id="",
        source=source,
        provider_id="1",
        asset_type=asset_type,
        url="https://example.com/asset.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        width=width,
        height=height,
        duration=duration,
    )


# --- rank() ---

def test_rank_empty_returns_empty() -> None:
    ranker = AssetRanker()
    assert ranker.rank(_make_scene(), []) == []


def test_rank_returns_all_assets() -> None:
    ranker = AssetRanker()
    assets = [_make_asset(), _make_asset(), _make_asset()]
    result = ranker.rank(_make_scene(), assets)
    assert len(result) == len(assets)


def test_rank_is_deterministic() -> None:
    ranker = AssetRanker()
    scene = _make_scene()
    assets = [
        _make_asset(asset_type="video", width=1920, height=1080, duration=5.0),
        _make_asset(asset_type="photo", width=1080, height=1920),
        _make_asset(asset_type="photo", width=640, height=480),
    ]
    assert ranker.rank(scene, assets) == ranker.rank(scene, assets)


def test_rank_single_asset_returns_it() -> None:
    ranker = AssetRanker()
    asset = _make_asset()
    assert ranker.rank(_make_scene(), [asset]) == [asset]


# --- Orientation ---

def test_portrait_beats_landscape() -> None:
    portrait = _make_asset(width=1080, height=1920)  # ratio 0.56 → portrait
    landscape = _make_asset(width=1920, height=1080)  # ratio 1.78 → landscape
    ranker = AssetRanker()
    result = ranker.rank(_make_scene(), [landscape, portrait])
    assert result[0] is portrait


def test_portrait_beats_square() -> None:
    portrait = _make_asset(width=1080, height=1920)
    square = _make_asset(width=1080, height=1080)
    ranker = AssetRanker()
    result = ranker.rank(_make_scene(), [square, portrait])
    assert result[0] is portrait


def test_square_beats_landscape() -> None:
    square = _make_asset(width=1080, height=1080)
    landscape = _make_asset(width=1920, height=1080)
    ranker = AssetRanker()
    result = ranker.rank(_make_scene(), [landscape, square])
    assert result[0] is square


def test_score_orientation_portrait() -> None:
    asset = _make_asset(width=1080, height=1920)
    assert _score_orientation(asset) == 30.0


def test_score_orientation_landscape() -> None:
    asset = _make_asset(width=1920, height=1080)
    assert _score_orientation(asset) == 5.0


def test_score_orientation_square() -> None:
    asset = _make_asset(width=1080, height=1080)
    assert _score_orientation(asset) == 15.0


def test_score_orientation_no_dimensions() -> None:
    asset = _make_asset(width=None, height=None)
    assert _score_orientation(asset) == 0.0


# --- Asset type ---

def test_video_beats_photo() -> None:
    video = _make_asset(asset_type="video", duration=5.0)
    photo = _make_asset(asset_type="photo")
    ranker = AssetRanker()
    # Use emotion with low video affinity so the emotion term doesn't dominate
    result = ranker.rank(_make_scene(emotion=Emotion.NOSTALGIA), [photo, video])
    assert result[0] is video


def test_photo_beats_vector() -> None:
    photo = _make_asset(asset_type="photo")
    vector = _make_asset(asset_type="vector")
    ranker = AssetRanker()
    result = ranker.rank(_make_scene(), [vector, photo])
    assert result[0] is photo


def test_score_asset_type_video() -> None:
    assert _score_asset_type(_make_asset(asset_type="video")) == 20.0


def test_score_asset_type_photo() -> None:
    assert _score_asset_type(_make_asset(asset_type="photo")) == 10.0


def test_score_asset_type_illustration() -> None:
    assert _score_asset_type(_make_asset(asset_type="illustration")) == 8.0


def test_score_asset_type_unknown_defaults() -> None:
    assert _score_asset_type(_make_asset(asset_type="psd")) == 5.0


# --- Resolution ---

def test_higher_resolution_beats_lower() -> None:
    hi_res = _make_asset(width=1920, height=1080)   # 2,073,600 px
    lo_res = _make_asset(width=320, height=240)      # 76,800 px
    ranker = AssetRanker()
    result = ranker.rank(_make_scene(), [lo_res, hi_res])
    assert result[0] is hi_res


def test_score_resolution_hd_is_max() -> None:
    asset = _make_asset(width=1920, height=1080)
    assert _score_resolution(asset) == 20.0


def test_score_resolution_no_dimensions_is_zero() -> None:
    asset = _make_asset(width=None, height=None)
    assert _score_resolution(asset) == 0.0


def test_score_resolution_low_res_is_partial() -> None:
    asset = _make_asset(width=960, height=540)  # quarter of 1920x1080
    score = _score_resolution(asset)
    assert 0.0 < score < 20.0


# --- Duration ---

def test_exact_duration_match_scores_max() -> None:
    asset = _make_asset(asset_type="video", duration=5.0)
    scene = _make_scene(duration_seconds=5.0)
    assert _score_duration(scene, asset) == 20.0


def test_image_duration_score_is_zero() -> None:
    asset = _make_asset(asset_type="photo", duration=None)
    scene = _make_scene(duration_seconds=5.0)
    assert _score_duration(scene, asset) == 0.0


def test_very_different_duration_scores_zero() -> None:
    asset = _make_asset(asset_type="video", duration=100.0)
    scene = _make_scene(duration_seconds=5.0)
    assert _score_duration(scene, asset) == 0.0


def test_closer_duration_beats_farther() -> None:
    close = _make_asset(asset_type="video", duration=6.0)   # 1s off from 5s
    far = _make_asset(asset_type="video", duration=10.0)    # 5s off from 5s
    scene = _make_scene(duration_seconds=5.0)
    assert _score_duration(scene, close) > _score_duration(scene, far)


def test_duration_ranking_prefers_closer_match() -> None:
    close = _make_asset(asset_type="video", duration=5.5)
    far = _make_asset(asset_type="video", duration=15.0)
    ranker = AssetRanker()
    result = ranker.rank(_make_scene(duration_seconds=5.0), [far, close])
    assert result[0] is close


# --- Emotion ---

def test_grief_prefers_video() -> None:
    video_score = _score_emotion(_make_scene(emotion=Emotion.GRIEF), _make_asset(asset_type="video"))
    photo_score = _score_emotion(_make_scene(emotion=Emotion.GRIEF), _make_asset(asset_type="photo"))
    assert video_score > photo_score


def test_nostalgia_prefers_photo() -> None:
    video_score = _score_emotion(_make_scene(emotion=Emotion.NOSTALGIA), _make_asset(asset_type="video"))
    photo_score = _score_emotion(_make_scene(emotion=Emotion.NOSTALGIA), _make_asset(asset_type="photo"))
    assert photo_score > video_score


def test_emotion_score_bounded() -> None:
    for emotion in Emotion:
        for asset_type in ("video", "photo"):
            score = _score_emotion(_make_scene(emotion=emotion), _make_asset(asset_type=asset_type))
            assert 0.0 <= score <= 10.0


def test_emotion_affects_ranking_order() -> None:
    video = _make_asset(asset_type="video", width=1920, height=1080, duration=5.0)
    photo = _make_asset(asset_type="photo", width=1920, height=1080)
    ranker = AssetRanker()
    # For GRIEF (high video affinity), video should win
    grief_result = ranker.rank(_make_scene(emotion=Emotion.GRIEF, duration_seconds=5.0), [photo, video])
    assert grief_result[0] is video
