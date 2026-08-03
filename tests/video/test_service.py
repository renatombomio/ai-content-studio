"""Tests for RenderService."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_content_studio.core.exceptions import ProviderError, RendererError
from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story
from ai_content_studio.shared.models.timeline import SubtitleCue, Timeline, TimelineScene
from ai_content_studio.video.service import RenderService

_OUT = Path("/out/video.mp4")


def _make_scene(order: int = 1, narration: str = "A farmer plants a seed.") -> Scene:
    return Scene(
        order=order,
        narration=narration,
        visual_prompt="Seed in soil.",
        emotion=Emotion.HOPE,
        duration_seconds=5.0,
    )


def _make_story(*narrations: str) -> Story:
    scenes = [_make_scene(i + 1, n) for i, n in enumerate(narrations or ("A farmer plants a seed.",))]
    return Story(title="T", hook="H.", caption="C.", hashtags=[], scenes=scenes)


def _minimal_timeline(story: Story) -> Timeline:
    return Timeline(
        story=story,
        scenes=[TimelineScene(scene=s, assets=[]) for s in story.scenes],
        duration=5.0,
    )


def _make_service(
    story: Story | None = None,
    cues: list[SubtitleCue] | None = None,
    output_path: Path = _OUT,
) -> tuple[RenderService, MagicMock, MagicMock, MagicMock, MagicMock]:
    s = story or _make_story()
    tl = _minimal_timeline(s)

    builder = MagicMock()
    voice = MagicMock()
    subtitles = MagicMock()
    renderer = MagicMock()

    builder.build.return_value = tl
    voice.generate.return_value = b"fake_audio"
    subtitles.generate.return_value = cues or []
    renderer.render.return_value = output_path

    svc = RenderService(
        timeline_builder=builder,
        voice_provider=voice,
        subtitle_generator=subtitles,
        renderer=renderer,
    )
    return svc, builder, voice, subtitles, renderer


# --- Orchestration calls ---

def test_timeline_builder_called_once(tmp_path: Path) -> None:
    story = _make_story()
    assets: dict[str, list[Asset]] = {}
    svc, builder, *_ = _make_service(story=story)
    svc.render(story, assets, tmp_path / "out.mp4")
    builder.build.assert_called_once_with(story, assets)


def test_voice_provider_called_once(tmp_path: Path) -> None:
    svc, _, voice, *_ = _make_service()
    svc.render(_make_story(), {}, tmp_path / "out.mp4")
    voice.generate.assert_called_once()


def test_voice_provider_receives_scene_narrations(tmp_path: Path) -> None:
    story = _make_story("First narration.", "Second narration.")
    svc, _, voice, *_ = _make_service(story=story)
    svc.render(story, {}, tmp_path / "out.mp4")
    passed_text: str = voice.generate.call_args[0][0]
    assert "First narration." in passed_text
    assert "Second narration." in passed_text


def test_subtitle_generator_called_once(tmp_path: Path) -> None:
    svc, _, _, subtitle_gen, _ = _make_service()
    svc.render(_make_story(), {}, tmp_path / "out.mp4")
    subtitle_gen.generate.assert_called_once()


def test_renderer_called_once(tmp_path: Path) -> None:
    svc, *_, renderer = _make_service()
    svc.render(_make_story(), {}, tmp_path / "out.mp4")
    renderer.render.assert_called_once()


# --- Timeline population ---

def test_renderer_receives_timeline_with_voice_track(tmp_path: Path) -> None:
    svc, *_, renderer = _make_service()
    svc.render(_make_story(), {}, tmp_path / "out.mp4")
    passed_timeline: Timeline = renderer.render.call_args[0][0]
    assert passed_timeline.voice_track is not None


def test_renderer_receives_voice_track_with_audio_bytes(tmp_path: Path) -> None:
    svc, *_, renderer = _make_service()
    svc.render(_make_story(), {}, tmp_path / "out.mp4")
    passed_timeline: Timeline = renderer.render.call_args[0][0]
    assert passed_timeline.voice_track is not None
    assert passed_timeline.voice_track.audio == b"fake_audio"


def test_renderer_receives_timeline_with_subtitles(tmp_path: Path) -> None:
    cues = [SubtitleCue(text="Hello.", start_time=0.0, end_time=2.0)]
    svc, *_, renderer = _make_service(cues=cues)
    svc.render(_make_story(), {}, tmp_path / "out.mp4")
    passed_timeline: Timeline = renderer.render.call_args[0][0]
    assert passed_timeline.subtitles == cues


def test_renderer_receives_correct_output_path(tmp_path: Path) -> None:
    out = tmp_path / "final.mp4"
    svc, *_, renderer = _make_service()
    svc.render(_make_story(), {}, out)
    assert renderer.render.call_args[0][1] == out


# --- Return value ---

def test_render_returns_output_path(tmp_path: Path) -> None:
    out = tmp_path / "video.mp4"
    svc, *_, renderer = _make_service(output_path=out)
    renderer.render.return_value = out
    result = svc.render(_make_story(), {}, out)
    assert result == out


# --- Exception propagation ---

def test_renderer_error_propagates(tmp_path: Path) -> None:
    svc, *_, renderer = _make_service()
    renderer.render.side_effect = RendererError("render failed")
    with pytest.raises(RendererError):
        svc.render(_make_story(), {}, tmp_path / "out.mp4")


def test_provider_error_propagates(tmp_path: Path) -> None:
    svc, _, voice, *_ = _make_service()
    voice.generate.side_effect = ProviderError("tts failed")
    with pytest.raises(ProviderError):
        svc.render(_make_story(), {}, tmp_path / "out.mp4")
