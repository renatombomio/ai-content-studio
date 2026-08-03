"""Tests for SubtitleGenerator."""

from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story
from ai_content_studio.shared.models.timeline import Timeline, TimelineAsset, TimelineScene
from ai_content_studio.video.subtitles import SubtitleGenerator

_LONG_NARRATION = (
    "Deep in the rainforest of Ghana, farmers have been growing cocoa for generations. "
    "Every pod is harvested by hand, a labour of love passed down from parent to child. "
    "The rich aroma of fermented cocoa fills the air as the sun rises over the canopy."
)


def _make_asset(start: float, end: float) -> Asset:
    return Asset(
        scene_id="",
        source="pexels",
        provider_id="1",
        asset_type="video",
        url="https://pexels.com/1.mp4",
        thumbnail_url="https://pexels.com/1_thumb.jpg",
    )


def _make_timeline_asset(start: float, end: float) -> TimelineAsset:
    return TimelineAsset(asset=_make_asset(start, end), start_time=start, end_time=end)


def _make_scene(narration: str, order: int = 1) -> Scene:
    return Scene(
        order=order,
        narration=narration,
        visual_prompt="Hands pressing seed into soil.",
        emotion=Emotion.HOPE,
        duration_seconds=5.0,
    )


def _make_timeline_scene(narration: str, start: float, end: float, order: int = 1) -> TimelineScene:
    scene = _make_scene(narration, order)
    return TimelineScene(scene=scene, assets=[_make_timeline_asset(start, end)])


def _make_timeline(*timeline_scenes: TimelineScene) -> Timeline:
    duration = timeline_scenes[-1].assets[0].end_time if timeline_scenes else 0.0
    scenes = list(timeline_scenes)
    story = Story(
        title="Test",
        hook="Hook.",
        caption="Caption.",
        hashtags=[],
        scenes=[ts.scene for ts in scenes],
    )
    return Timeline(story=story, scenes=scenes, duration=duration)


# --- Basic generation ---

def test_generate_returns_list() -> None:
    tl = _make_timeline(_make_timeline_scene("Hello world.", 0.0, 5.0))
    cues = SubtitleGenerator().generate(tl)
    assert isinstance(cues, list)


def test_short_narration_produces_one_cue() -> None:
    tl = _make_timeline(_make_timeline_scene("A farmer plants a seed.", 0.0, 5.0))
    cues = SubtitleGenerator().generate(tl)
    assert len(cues) == 1


def test_cue_text_contains_narration() -> None:
    tl = _make_timeline(_make_timeline_scene("A farmer plants a seed.", 0.0, 5.0))
    cue = SubtitleGenerator().generate(tl)[0]
    assert "farmer" in cue.text


def test_empty_timeline_returns_empty() -> None:
    story = Story(title="T", hook="H.", caption="C.", hashtags=[], scenes=[])
    tl = Timeline(story=story, scenes=[], duration=0.0)
    assert SubtitleGenerator().generate(tl) == []


def test_empty_narration_produces_no_cues() -> None:
    tl = _make_timeline(_make_timeline_scene("", 0.0, 5.0))
    assert SubtitleGenerator().generate(tl) == []


# --- Ordering ---

def test_cues_are_in_chronological_order() -> None:
    ts1 = _make_timeline_scene("Scene one narration.", 0.0, 5.0, order=1)
    ts2 = _make_timeline_scene("Scene two narration.", 5.0, 10.0, order=2)
    tl = _make_timeline(ts1, ts2)
    cues = SubtitleGenerator().generate(tl)
    starts = [c.start_time for c in cues]
    assert starts == sorted(starts)


def test_multiple_scenes_produce_ordered_cues() -> None:
    ts1 = _make_timeline_scene("First scene.", 0.0, 3.0, order=1)
    ts2 = _make_timeline_scene("Second scene.", 3.0, 6.0, order=2)
    ts3 = _make_timeline_scene("Third scene.", 6.0, 9.0, order=3)
    tl = _make_timeline(ts1, ts2, ts3)
    cues = SubtitleGenerator().generate(tl)
    for i in range(len(cues) - 1):
        assert cues[i].end_time <= cues[i + 1].start_time


# --- Timing ---

def test_first_cue_starts_at_scene_start() -> None:
    tl = _make_timeline(_make_timeline_scene("Narration text.", 2.0, 7.0))
    cues = SubtitleGenerator().generate(tl)
    assert cues[0].start_time == 2.0


def test_last_cue_ends_exactly_at_scene_end() -> None:
    tl = _make_timeline(_make_timeline_scene("Narration text.", 0.0, 10.0))
    cues = SubtitleGenerator().generate(tl)
    assert cues[-1].end_time == 10.0


def test_cues_do_not_overlap() -> None:
    tl = _make_timeline(_make_timeline_scene(_LONG_NARRATION, 0.0, 30.0))
    cues = SubtitleGenerator().generate(tl)
    for i in range(len(cues) - 1):
        assert cues[i].end_time <= cues[i + 1].start_time


def test_all_cues_within_scene_bounds() -> None:
    tl = _make_timeline(_make_timeline_scene(_LONG_NARRATION, 5.0, 35.0))
    cues = SubtitleGenerator().generate(tl)
    for cue in cues:
        assert cue.start_time >= 5.0
        assert cue.end_time <= 35.0


def test_cue_end_greater_than_start() -> None:
    tl = _make_timeline(_make_timeline_scene("Hello world.", 0.0, 5.0))
    for cue in SubtitleGenerator().generate(tl):
        assert cue.end_time > cue.start_time


# --- Splitting ---

def test_long_narration_splits_into_multiple_cues() -> None:
    tl = _make_timeline(_make_timeline_scene(_LONG_NARRATION, 0.0, 30.0))
    cues = SubtitleGenerator().generate(tl)
    assert len(cues) > 1


def test_no_cue_exceeds_max_chars() -> None:
    tl = _make_timeline(_make_timeline_scene(_LONG_NARRATION, 0.0, 30.0))
    for cue in SubtitleGenerator().generate(tl):
        assert len(cue.text) <= 84


def test_two_short_sentences_merge_into_one_cue() -> None:
    tl = _make_timeline(_make_timeline_scene("Hi there. Good morning.", 0.0, 5.0))
    cues = SubtitleGenerator().generate(tl)
    assert len(cues) == 1


def test_scene_without_assets_still_produces_cues() -> None:
    scene = _make_scene("A farmer plants a seed.")
    story = Story(title="T", hook="H.", caption="C.", hashtags=[], scenes=[scene])
    ts = TimelineScene(scene=scene, assets=[])
    tl = Timeline(story=story, scenes=[ts], duration=5.0)
    cues = SubtitleGenerator().generate(tl)
    assert len(cues) >= 1


# --- Determinism ---

def test_generate_is_deterministic() -> None:
    tl = _make_timeline(_make_timeline_scene(_LONG_NARRATION, 0.0, 30.0))
    gen = SubtitleGenerator()
    assert gen.generate(tl) == gen.generate(tl)


def test_same_input_produces_same_cue_count() -> None:
    tl = _make_timeline(_make_timeline_scene(_LONG_NARRATION, 0.0, 30.0))
    gen = SubtitleGenerator()
    assert len(gen.generate(tl)) == len(gen.generate(tl))
