"""Tests for FFmpegRenderer."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story
from ai_content_studio.shared.models.timeline import (
    Timeline,
    TimelineAsset,
    TimelineScene,
    VoiceTrack,
)
from ai_content_studio.video.renderer import FFmpegRenderer

_PATCH = "ai_content_studio.video.renderer.subprocess.run"


def _make_asset(path: str = "/tmp/clip.mp4", asset_type: str = "video") -> Asset:
    return Asset(
        scene_id="",
        source="pexels",
        provider_id="1",
        asset_type=asset_type,
        url="https://pexels.com/1.mp4",
        thumbnail_url="https://pexels.com/1_thumb.jpg",
        path=path,
    )


def _make_scene(order: int = 1) -> Scene:
    return Scene(
        order=order,
        narration="A farmer plants a seed at dawn.",
        visual_prompt="Hands pressing seed into soil.",
        emotion=Emotion.HOPE,
        duration_seconds=5.0,
    )


def _make_timeline_scene(
    path: str = "/tmp/clip.mp4",
    asset_type: str = "video",
    start: float = 0.0,
    end: float = 5.0,
    order: int = 1,
) -> TimelineScene:
    scene = _make_scene(order)
    asset = _make_asset(path, asset_type)
    ta = TimelineAsset(asset=asset, start_time=start, end_time=end)
    return TimelineScene(scene=scene, assets=[ta])


def _make_timeline(*tscenes: TimelineScene, voice: bool = False) -> Timeline:
    story = Story(
        title="The Seed",
        hook="Hook.",
        caption="Caption.",
        hashtags=[],
        scenes=[ts.scene for ts in tscenes],
    )
    duration = tscenes[-1].assets[0].end_time if tscenes else 0.0
    vt = VoiceTrack(audio=b"RIFF....", sample_rate=24000, duration=duration) if voice else None
    return Timeline(story=story, scenes=list(tscenes), duration=duration, voice_track=vt)


def _ok_run() -> MagicMock:
    m = MagicMock()
    m.returncode = 0
    return m


# --- Return value ---

def test_render_returns_output_path(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    out = tmp_path / "out.mp4"
    with patch(_PATCH, return_value=_ok_run()):
        result = FFmpegRenderer().render(tl, out)
    assert result == out


# --- FFmpeg invocation ---

def test_render_calls_subprocess_run(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    mock_run.assert_called_once()


def test_command_starts_with_ffmpeg(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "ffmpeg"


def test_command_includes_output_path(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    out = tmp_path / "out.mp4"
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, out)
    cmd = mock_run.call_args[0][0]
    assert str(out) in cmd


def test_command_includes_asset_path(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene(path="/media/clip.mp4"))
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "/media/clip.mp4" in cmd


def test_command_includes_libx264(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "libx264" in cmd


def test_command_includes_overwrite_flag(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = mock_run.call_args[0][0]
    assert "-y" in cmd


def test_command_includes_duration(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene(start=0.0, end=7.5))
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "7.5" in cmd


# --- Audio ---

def test_command_includes_audio_when_voice_track_present(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene(), voice=True)
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "aac" in cmd


def test_command_has_no_audio_without_voice_track(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene(), voice=False)
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "aac" not in cmd


# --- Multiple scenes ---

def test_command_includes_all_asset_paths(tmp_path: Path) -> None:
    ts1 = _make_timeline_scene(path="/media/a.mp4", start=0.0, end=5.0, order=1)
    ts2 = _make_timeline_scene(path="/media/b.mp4", start=5.0, end=10.0, order=2)
    tl = _make_timeline(ts1, ts2)
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "/media/a.mp4" in cmd
    assert "/media/b.mp4" in cmd


# --- Image asset ---

def test_image_asset_includes_loop_flag(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene(path="/media/img.jpg", asset_type="photo"))
    with patch(_PATCH, return_value=_ok_run()) as mock_run:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    cmd = " ".join(mock_run.call_args[0][0])
    assert "-loop" in cmd


# --- Validation errors ---

def test_empty_timeline_raises_renderer_error(tmp_path: Path) -> None:
    story = Story(title="T", hook="H.", caption="C.", hashtags=[], scenes=[])
    tl = Timeline(story=story, scenes=[], duration=0.0)
    with pytest.raises(RendererError):
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")


def test_scene_with_no_path_raises_renderer_error(tmp_path: Path) -> None:
    scene = _make_scene()
    asset = Asset(
        scene_id="", source="pexels", provider_id="1",
        asset_type="video", url="https://x.com/1.mp4",
        thumbnail_url="https://x.com/1t.jpg", path=None,
    )
    ta = TimelineAsset(asset=asset, start_time=0.0, end_time=5.0)
    story = Story(title="T", hook="H.", caption="C.", hashtags=[], scenes=[scene])
    tl = Timeline(story=story, scenes=[TimelineScene(scene=scene, assets=[ta])], duration=5.0)
    with pytest.raises(RendererError):
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")


def test_scene_with_no_assets_raises_renderer_error(tmp_path: Path) -> None:
    scene = _make_scene()
    story = Story(title="T", hook="H.", caption="C.", hashtags=[], scenes=[scene])
    tl = Timeline(story=story, scenes=[TimelineScene(scene=scene, assets=[])], duration=5.0)
    with pytest.raises(RendererError):
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")


# --- Subprocess failures ---

def test_ffmpeg_failure_raises_renderer_error(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    error = subprocess.CalledProcessError(1, ["ffmpeg"], stderr=b"error output")
    with patch(_PATCH, side_effect=error), pytest.raises(RendererError):
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")


def test_ffmpeg_not_found_raises_renderer_error(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    with patch(_PATCH, side_effect=FileNotFoundError()), pytest.raises(RendererError):
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")


def test_renderer_error_wraps_original_exception(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    error = subprocess.CalledProcessError(2, ["ffmpeg"], stderr=b"bad codec")
    with patch(_PATCH, side_effect=error), pytest.raises(RendererError) as exc_info:
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
    assert exc_info.value.__cause__ is not None


def test_os_error_raises_renderer_error(tmp_path: Path) -> None:
    tl = _make_timeline(_make_timeline_scene())
    with patch(_PATCH, side_effect=OSError("permission denied")), pytest.raises(RendererError):
        FFmpegRenderer().render(tl, tmp_path / "out.mp4")
