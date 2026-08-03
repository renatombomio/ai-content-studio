"""Tests for Timeline domain models."""

from ai_content_studio.shared.models import (
    SubtitleCue,
    Timeline,
    TimelineAsset,
    TimelineScene,
    VoiceTrack,
)
from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story


def _make_asset(provider_id: str = "1") -> Asset:
    return Asset(
        scene_id="",
        source="pexels",
        provider_id=provider_id,
        asset_type="video",
        url=f"https://pexels.com/{provider_id}.mp4",
        thumbnail_url=f"https://pexels.com/{provider_id}_thumb.jpg",
    )


def _make_scene(order: int = 1) -> Scene:
    return Scene(
        order=order,
        narration="A farmer plants a seed.",
        visual_prompt="Hands pressing seed into soil.",
        emotion=Emotion.HOPE,
        duration_seconds=5.0,
    )


def _make_story() -> Story:
    return Story(
        title="The Seed",
        hook="Every great harvest begins with a single seed.",
        caption="Watch how cocoa changes lives.",
        hashtags=["#cocoa", "#farming"],
        scenes=[_make_scene(1), _make_scene(2)],
    )


# --- TimelineAsset ---

def test_timeline_asset_creation() -> None:
    asset = TimelineAsset(asset=_make_asset(), start_time=0.0, end_time=5.0)
    assert asset.start_time == 0.0
    assert asset.end_time == 5.0


def test_timeline_asset_holds_asset() -> None:
    a = _make_asset("42")
    ta = TimelineAsset(asset=a, start_time=0.0, end_time=5.0)
    assert ta.asset.provider_id == "42"


def test_timeline_asset_start_end_preserved() -> None:
    ta = TimelineAsset(asset=_make_asset(), start_time=2.5, end_time=7.5)
    assert ta.start_time == 2.5
    assert ta.end_time == 7.5


# --- TimelineScene ---

def test_timeline_scene_creation() -> None:
    ts = TimelineScene(scene=_make_scene(), assets=[])
    assert ts.assets == []


def test_timeline_scene_holds_scene() -> None:
    scene = _make_scene(order=3)
    ts = TimelineScene(scene=scene, assets=[])
    assert ts.scene.order == 3


def test_timeline_scene_holds_assets() -> None:
    ta1 = TimelineAsset(asset=_make_asset("1"), start_time=0.0, end_time=5.0)
    ta2 = TimelineAsset(asset=_make_asset("2"), start_time=5.0, end_time=10.0)
    ts = TimelineScene(scene=_make_scene(), assets=[ta1, ta2])
    assert len(ts.assets) == 2


def test_timeline_scene_asset_order_preserved() -> None:
    ta1 = TimelineAsset(asset=_make_asset("1"), start_time=0.0, end_time=5.0)
    ta2 = TimelineAsset(asset=_make_asset("2"), start_time=5.0, end_time=10.0)
    ts = TimelineScene(scene=_make_scene(), assets=[ta1, ta2])
    assert ts.assets[0].asset.provider_id == "1"
    assert ts.assets[1].asset.provider_id == "2"


# --- Timeline ---

def test_timeline_creation() -> None:
    tl = Timeline(story=_make_story(), scenes=[], duration=0.0)
    assert tl.scenes == []
    assert tl.duration == 0.0


def test_timeline_holds_story() -> None:
    story = _make_story()
    tl = Timeline(story=story, scenes=[], duration=0.0)
    assert tl.story.title == "The Seed"


def test_timeline_duration_preserved() -> None:
    tl = Timeline(story=_make_story(), scenes=[], duration=30.5)
    assert tl.duration == 30.5


def test_timeline_scene_order_preserved() -> None:
    ts1 = TimelineScene(scene=_make_scene(1), assets=[])
    ts2 = TimelineScene(scene=_make_scene(2), assets=[])
    tl = Timeline(story=_make_story(), scenes=[ts1, ts2], duration=10.0)
    assert tl.scenes[0].scene.order == 1
    assert tl.scenes[1].scene.order == 2


def test_timeline_full_structure() -> None:
    ta = TimelineAsset(asset=_make_asset(), start_time=0.0, end_time=5.0)
    ts = TimelineScene(scene=_make_scene(), assets=[ta])
    tl = Timeline(story=_make_story(), scenes=[ts], duration=5.0)
    assert len(tl.scenes) == 1
    assert len(tl.scenes[0].assets) == 1


# --- Serialization ---

def test_timeline_serializes_to_dict() -> None:
    tl = Timeline(story=_make_story(), scenes=[], duration=10.0)
    data = tl.model_dump()
    assert "story" in data
    assert "scenes" in data
    assert "duration" in data


def test_timeline_roundtrips_via_model_dump() -> None:
    ta = TimelineAsset(asset=_make_asset(), start_time=0.0, end_time=5.0)
    ts = TimelineScene(scene=_make_scene(), assets=[ta])
    tl = Timeline(story=_make_story(), scenes=[ts], duration=5.0)
    data = tl.model_dump()
    tl2 = Timeline.model_validate(data)
    assert tl2.duration == tl.duration
    assert tl2.scenes[0].assets[0].end_time == 5.0


# --- VoiceTrack ---

def test_voice_track_creation() -> None:
    vt = VoiceTrack(audio=b"RIFF....", sample_rate=24000, duration=5.0)
    assert vt.sample_rate == 24000
    assert vt.duration == 5.0
    assert vt.audio == b"RIFF...."


def test_voice_track_audio_is_bytes() -> None:
    vt = VoiceTrack(audio=b"\x00\x01\x02", sample_rate=24000, duration=1.0)
    assert isinstance(vt.audio, bytes)


# --- SubtitleCue ---

def test_subtitle_cue_creation() -> None:
    cue = SubtitleCue(text="A farmer plants a seed.", start_time=0.0, end_time=3.0)
    assert cue.text == "A farmer plants a seed."
    assert cue.start_time == 0.0
    assert cue.end_time == 3.0


def test_subtitle_cue_preserves_timing() -> None:
    cue = SubtitleCue(text="hello", start_time=1.5, end_time=4.25)
    assert cue.start_time == 1.5
    assert cue.end_time == 4.25


# --- Timeline with voice_track and subtitles ---

def test_timeline_voice_track_defaults_none() -> None:
    tl = Timeline(story=_make_story(), scenes=[], duration=0.0)
    assert tl.voice_track is None


def test_timeline_subtitles_defaults_empty() -> None:
    tl = Timeline(story=_make_story(), scenes=[], duration=0.0)
    assert tl.subtitles == []


def test_timeline_accepts_voice_track() -> None:
    vt = VoiceTrack(audio=b"audio", sample_rate=24000, duration=10.0)
    tl = Timeline(story=_make_story(), scenes=[], duration=10.0, voice_track=vt)
    assert tl.voice_track is not None
    assert tl.voice_track.sample_rate == 24000


def test_timeline_accepts_subtitles() -> None:
    cues = [
        SubtitleCue(text="First line.", start_time=0.0, end_time=2.0),
        SubtitleCue(text="Second line.", start_time=2.0, end_time=5.0),
    ]
    tl = Timeline(story=_make_story(), scenes=[], duration=5.0, subtitles=cues)
    assert len(tl.subtitles) == 2
    assert tl.subtitles[0].text == "First line."


def test_timeline_existing_fields_unchanged() -> None:
    vt = VoiceTrack(audio=b"x", sample_rate=24000, duration=5.0)
    cues = [SubtitleCue(text="hi", start_time=0.0, end_time=1.0)]
    tl = Timeline(story=_make_story(), scenes=[], duration=5.0, voice_track=vt, subtitles=cues)
    assert tl.duration == 5.0
    assert tl.story.title == "The Seed"
