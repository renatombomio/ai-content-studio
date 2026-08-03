"""End-to-end render pipeline tests using real components (FFmpegRenderer mocked)."""

import io
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import soundfile as sf  # type: ignore[import-untyped]

from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story
from ai_content_studio.shared.models.timeline import Timeline
from ai_content_studio.video.renderer import FFmpegRenderer
from ai_content_studio.video.service import RenderService
from ai_content_studio.video.subtitles import SubtitleGenerator
from ai_content_studio.video.timeline_builder import TimelineBuilder
from ai_content_studio.video.voice.interface import VoiceProvider

_SAMPLE_RATE = 24_000


class FakeVoiceProvider(VoiceProvider):
    """Returns valid WAV bytes for any text."""

    def generate(self, text: str) -> bytes:
        samples = np.zeros(_SAMPLE_RATE, dtype=np.float32)  # 1 second of silence
        buf = io.BytesIO()
        sf.write(buf, samples, _SAMPLE_RATE, format="WAV")
        return buf.getvalue()


def _make_asset(scene_id: str, path: str = "/fake/clip.mp4") -> Asset:
    return Asset(
        scene_id=scene_id,
        source="pexels",
        provider_id="1",
        asset_type="video",
        url="https://pexels.com/1.mp4",
        thumbnail_url="https://pexels.com/1_thumb.jpg",
        path=path,
    )


def _make_story() -> Story:
    scenes = [
        Scene(
            order=1,
            narration="A farmer plants a seed at dawn.",
            visual_prompt="Hands pressing seed into rich soil.",
            emotion=Emotion.HOPE,
            duration_seconds=5.0,
        ),
        Scene(
            order=2,
            narration="The rains come and the seed begins to sprout.",
            visual_prompt="Rain falling on green shoots.",
            emotion=Emotion.LONGING,
            duration_seconds=6.0,
        ),
    ]
    return Story(
        title="The Cocoa Seed",
        hook="Every great harvest begins with a single seed.",
        caption="Watch how cocoa changes lives.",
        hashtags=["#cocoa", "#farming"],
        scenes=scenes,
    )


def _make_pipeline(tmp_path: Path) -> tuple[RenderService, MagicMock]:
    renderer_mock = MagicMock(spec=FFmpegRenderer)
    out = tmp_path / "video.mp4"
    renderer_mock.render.return_value = out

    service = RenderService(
        timeline_builder=TimelineBuilder(),
        voice_provider=FakeVoiceProvider(),
        subtitle_generator=SubtitleGenerator(),
        renderer=renderer_mock,
    )
    return service, renderer_mock


# --- Pipeline output ---

def test_pipeline_returns_output_path(tmp_path: Path) -> None:
    svc, _ = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    out = tmp_path / "video.mp4"
    result = svc.render(story, assets, out)
    assert result == out


# --- Voice track ---

def test_pipeline_voice_track_populated(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    passed: Timeline = renderer_mock.render.call_args[0][0]
    assert passed.voice_track is not None


def test_pipeline_voice_track_has_valid_sample_rate(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    passed: Timeline = renderer_mock.render.call_args[0][0]
    assert passed.voice_track is not None
    assert passed.voice_track.sample_rate == _SAMPLE_RATE


def test_pipeline_voice_track_duration_positive(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    passed: Timeline = renderer_mock.render.call_args[0][0]
    assert passed.voice_track is not None
    assert passed.voice_track.duration > 0.0


# --- Subtitles ---

def test_pipeline_subtitles_populated(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    passed: Timeline = renderer_mock.render.call_args[0][0]
    assert len(passed.subtitles) > 0


def test_pipeline_subtitles_are_ordered(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    passed: Timeline = renderer_mock.render.call_args[0][0]
    starts = [c.start_time for c in passed.subtitles]
    assert starts == sorted(starts)


def test_pipeline_subtitles_cover_narration(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    passed: Timeline = renderer_mock.render.call_args[0][0]
    all_text = " ".join(c.text for c in passed.subtitles)
    assert "farmer" in all_text
    assert "seed" in all_text


# --- Component wiring ---

def test_pipeline_renderer_called_once(tmp_path: Path) -> None:
    svc, renderer_mock = _make_pipeline(tmp_path)
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}
    svc.render(story, assets, tmp_path / "video.mp4")
    renderer_mock.render.assert_called_once()


# --- Determinism ---

def test_pipeline_is_deterministic(tmp_path: Path) -> None:
    story = _make_story()
    assets = {s.id: [_make_asset(s.id)] for s in story.scenes}

    svc1, mock1 = _make_pipeline(tmp_path)
    svc1.render(story, assets, tmp_path / "v1.mp4")
    tl1: Timeline = mock1.render.call_args[0][0]

    svc2, mock2 = _make_pipeline(tmp_path)
    svc2.render(story, assets, tmp_path / "v2.mp4")
    tl2: Timeline = mock2.render.call_args[0][0]

    assert tl1.duration == tl2.duration
    assert len(tl1.subtitles) == len(tl2.subtitles)
