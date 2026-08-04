"""Tests for ReflectionRenderer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.video.reflection_renderer import (
    ReflectionRenderer,
    _build_command,
    _wrap_text,
)


def _asset(tmp_path: Path, name: str = "asset.mp4") -> Path:
    p = tmp_path / name
    p.write_bytes(b"fake")
    return p


# --- text wrapping ---

def test_wrap_text_short_fits_one_line() -> None:
    result = _wrap_text("Una sola línea.")
    assert "\n" not in result


def test_wrap_text_long_wraps() -> None:
    long_text = "Este es un texto que debería romper en múltiples líneas porque es bastante largo."
    result = _wrap_text(long_text)
    assert "\n" in result


def test_wrap_text_preserves_content() -> None:
    text = "Hubo un día que nunca olvidaste."
    result = _wrap_text(text)
    for word in text.split():
        assert word in result


# --- command construction ---

def test_command_uses_stream_loop_for_video(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    cmd = _build_command(asset, "Texto", tmp_path / "out.mp4", 12.0, "video")
    assert "-stream_loop" in cmd
    assert "-1" in cmd


def test_command_uses_loop_for_photo(tmp_path: Path) -> None:
    asset = _asset(tmp_path, "asset.jpg")
    cmd = _build_command(asset, "Texto", tmp_path / "out.mp4", 12.0, "photo")
    assert "-loop" in cmd
    assert "-stream_loop" not in cmd


def test_command_includes_duration(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    cmd = _build_command(asset, "Texto", tmp_path / "out.mp4", 14.0, "video")
    assert "-t" in cmd
    idx = cmd.index("-t")
    assert cmd[idx + 1] == "14.0"


def test_command_targets_output_path(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    out = tmp_path / "reflection.mp4"
    cmd = _build_command(asset, "Texto", out, 12.0, "video")
    assert str(out) in cmd


def test_command_includes_drawtext(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    cmd = _build_command(asset, "Texto de prueba", tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "drawtext" in vf


def test_command_no_audio_flags(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    cmd = _build_command(asset, "Texto", tmp_path / "out.mp4", 12.0, "video")
    assert "-c:a" not in cmd
    assert "-map" not in cmd


# --- renderer ---

def test_renderer_raises_if_asset_missing(tmp_path: Path) -> None:
    renderer = ReflectionRenderer()
    with pytest.raises(RendererError, match="Asset not found"):
        renderer.render(
            asset_path=tmp_path / "missing.mp4",
            reflection_text="Texto",
            output_path=tmp_path / "out.mp4",
        )


def test_renderer_returns_output_path(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    out = tmp_path / "out.mp4"
    renderer = ReflectionRenderer()
    with patch("ai_content_studio.video.reflection_renderer._execute"):
        result = renderer.render(
            asset_path=asset,
            reflection_text="Una reflexión breve.",
            output_path=out,
        )
    assert result == out


def test_renderer_calls_ffmpeg_once(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    renderer = ReflectionRenderer()
    mock_execute = MagicMock()
    with patch("ai_content_studio.video.reflection_renderer._execute", mock_execute):
        renderer.render(
            asset_path=asset,
            reflection_text="Texto.",
            output_path=tmp_path / "out.mp4",
        )
    mock_execute.assert_called_once()
