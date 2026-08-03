"""Tests for TimelineBuilder."""

from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story
from ai_content_studio.video.timeline_builder import TimelineBuilder


def _make_scene(order: int, narration: str = "A farmer plants a seed at dawn.") -> Scene:
    return Scene(
        order=order,
        narration=narration,
        visual_prompt="Hands pressing seed into rich soil.",
        emotion=Emotion.HOPE,
        duration_seconds=5.0,
    )


def _make_asset(provider_id: str) -> Asset:
    return Asset(
        scene_id="",
        source="pexels",
        provider_id=provider_id,
        asset_type="video",
        url=f"https://pexels.com/{provider_id}.mp4",
        thumbnail_url=f"https://pexels.com/{provider_id}_thumb.jpg",
    )


def _make_story(*scenes: Scene) -> Story:
    return Story(
        title="The Seed",
        hook="Every great harvest begins with a single seed.",
        caption="Watch how cocoa changes lives.",
        hashtags=["#cocoa"],
        scenes=list(scenes),
    )


# --- All scenes present ---

def test_timeline_contains_all_scenes() -> None:
    s1, s2 = _make_scene(1), _make_scene(2)
    story = _make_story(s1, s2)
    tl = TimelineBuilder().build(story, {})
    assert len(tl.scenes) == 2


def test_timeline_single_scene() -> None:
    s = _make_scene(1)
    story = _make_story(s)
    tl = TimelineBuilder().build(story, {})
    assert len(tl.scenes) == 1


# --- Scene ordering ---

def test_scene_order_preserved() -> None:
    s1, s2, s3 = _make_scene(1), _make_scene(2), _make_scene(3)
    story = _make_story(s1, s2, s3)
    tl = TimelineBuilder().build(story, {})
    orders = [ts.scene.order for ts in tl.scenes]
    assert orders == [1, 2, 3]


# --- Asset attachment ---

def test_assets_attached_to_correct_scene() -> None:
    s1 = _make_scene(1)
    s2 = _make_scene(2)
    story = _make_story(s1, s2)
    a = _make_asset("42")
    tl = TimelineBuilder().build(story, {s2.id: [a]})
    assert tl.scenes[0].assets == []
    assert tl.scenes[1].assets[0].asset.provider_id == "42"


def test_multiple_assets_attached_to_scene() -> None:
    s = _make_scene(1)
    story = _make_story(s)
    assets = [_make_asset("1"), _make_asset("2")]
    tl = TimelineBuilder().build(story, {s.id: assets})
    assert len(tl.scenes[0].assets) == 2


def test_empty_assets_by_scene_supported() -> None:
    story = _make_story(_make_scene(1), _make_scene(2))
    tl = TimelineBuilder().build(story, {})
    assert all(ts.assets == [] for ts in tl.scenes)


# --- Timing ---

def test_first_scene_starts_at_zero() -> None:
    s = _make_scene(1)
    story = _make_story(s)
    a = _make_asset("1")
    tl = TimelineBuilder().build(story, {s.id: [a]})
    assert tl.scenes[0].assets[0].start_time == 0.0


def test_scene_start_times_are_sequential() -> None:
    s1, s2 = _make_scene(1), _make_scene(2)
    story = _make_story(s1, s2)
    a1, a2 = _make_asset("1"), _make_asset("2")
    tl = TimelineBuilder().build(story, {s1.id: [a1], s2.id: [a2]})
    end1 = tl.scenes[0].assets[0].end_time
    start2 = tl.scenes[1].assets[0].start_time
    assert start2 == end1


def test_no_time_gaps_between_scenes() -> None:
    scenes = [_make_scene(i) for i in range(1, 5)]
    story = _make_story(*scenes)
    assets_by_scene = {s.id: [_make_asset(str(i))] for i, s in enumerate(scenes)}
    tl = TimelineBuilder().build(story, assets_by_scene)
    for i in range(len(tl.scenes) - 1):
        end = tl.scenes[i].assets[0].end_time
        start = tl.scenes[i + 1].assets[0].start_time
        assert end == start


def test_asset_end_time_greater_than_start() -> None:
    s = _make_scene(1)
    story = _make_story(s)
    a = _make_asset("1")
    tl = TimelineBuilder().build(story, {s.id: [a]})
    ta = tl.scenes[0].assets[0]
    assert ta.end_time > ta.start_time


def test_all_assets_in_scene_share_same_interval() -> None:
    s = _make_scene(1)
    story = _make_story(s)
    assets = [_make_asset("1"), _make_asset("2")]
    tl = TimelineBuilder().build(story, {s.id: assets})
    ta1, ta2 = tl.scenes[0].assets
    assert ta1.start_time == ta2.start_time
    assert ta1.end_time == ta2.end_time


# --- Duration ---

def test_timeline_duration_equals_final_scene_end_time() -> None:
    s1, s2 = _make_scene(1), _make_scene(2)
    story = _make_story(s1, s2)
    a1, a2 = _make_asset("1"), _make_asset("2")
    tl = TimelineBuilder().build(story, {s1.id: [a1], s2.id: [a2]})
    assert tl.duration == tl.scenes[-1].assets[0].end_time


def test_timeline_duration_without_assets() -> None:
    s1, s2 = _make_scene(1), _make_scene(2)
    story = _make_story(s1, s2)
    tl = TimelineBuilder().build(story, {})
    assert tl.duration > 0.0


def test_minimum_scene_duration() -> None:
    s = _make_scene(1, narration="Hi.")
    story = _make_story(s)
    tl = TimelineBuilder().build(story, {})
    assert tl.duration >= 2.0


def test_longer_narration_produces_longer_duration() -> None:
    short = _make_scene(1, narration="Hello.")
    long_ = _make_scene(1, narration=" ".join(["word"] * 50))
    tl_short = TimelineBuilder().build(_make_story(short), {})
    tl_long = TimelineBuilder().build(_make_story(long_), {})
    assert tl_long.duration > tl_short.duration


# --- Determinism ---

def test_build_is_deterministic() -> None:
    s1, s2 = _make_scene(1), _make_scene(2)
    story = _make_story(s1, s2)
    assets = {s1.id: [_make_asset("1")], s2.id: [_make_asset("2")]}
    tl1 = TimelineBuilder().build(story, assets)
    tl2 = TimelineBuilder().build(story, assets)
    assert tl1.duration == tl2.duration
    assert tl1.scenes[0].assets[0].end_time == tl2.scenes[0].assets[0].end_time
