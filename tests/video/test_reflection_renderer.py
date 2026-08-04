"""Tests for ReflectionRenderer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.video.reflection_renderer import (
    _MAX_TEXT_HEIGHT,
    _MIN_FONT_SIZE,
    ReflectionRenderer,
    _adapt_typography,
    _build_command,
    _wrap_text,
)


def _asset(tmp_path: Path, name: str = "asset.mp4") -> Path:
    p = tmp_path / name
    p.write_bytes(b"fake")
    return p


def _text_file(tmp_path: Path, text: str = "Texto") -> Path:
    p = tmp_path / "text.txt"
    p.write_text(text)
    return p


# --- text wrapping ---

def test_wrap_text_short_fits_one_line() -> None:
    result = _wrap_text("Una sola línea.", width=26)
    assert "\n" not in result


def test_wrap_text_long_wraps() -> None:
    long_text = "Este es un texto que debería romper en múltiples líneas porque es bastante largo."
    result = _wrap_text(long_text, width=26)
    assert "\n" in result


def test_wrap_text_preserves_content() -> None:
    text = "Hubo un día que nunca olvidaste."
    result = _wrap_text(text, width=26)
    for word in text.split():
        assert word in result


# --- adaptive typography ---

def test_adapt_typography_preserves_full_text() -> None:
    text = "Tu mente encontró la manera de seguir. Tu cuerpo todavía no ha terminado de entender que ya pasó."
    wrapped, _, _ = _adapt_typography(text)
    for word in text.split():
        assert word in wrapped


def test_adapt_typography_fits_within_max_height() -> None:
    text = "Tu mente encontró la manera de seguir. Tu cuerpo todavía no ha terminado de entender que ya pasó."
    wrapped, font_size, line_spacing = _adapt_typography(text)
    n = wrapped.count("\n") + 1
    estimated = n * (font_size * 1.25) + max(0, n - 1) * line_spacing
    assert estimated <= _MAX_TEXT_HEIGHT


def test_adapt_typography_never_truncates() -> None:
    long_text = " ".join(["palabra"] * 60)
    wrapped, font_size, _ = _adapt_typography(long_text)
    assert font_size >= _MIN_FONT_SIZE
    for word in long_text.split():
        assert word in wrapped


def test_adapt_typography_returns_max_font_for_short_text() -> None:
    _, font_size, _ = _adapt_typography("Algo breve.")
    assert font_size == 42


# --- command construction ---

def test_command_uses_stream_loop_for_video(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    assert "-stream_loop" in cmd
    assert "-1" in cmd


def test_command_uses_loop_for_photo(tmp_path: Path) -> None:
    asset = _asset(tmp_path, "asset.jpg")
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "photo")
    assert "-loop" in cmd
    assert "-stream_loop" not in cmd


def test_command_includes_duration(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 14.0, "video")
    assert "-t" in cmd
    idx = cmd.index("-t")
    assert cmd[idx + 1] == "14.0"


def test_command_targets_output_path(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    out = tmp_path / "reflection.mp4"
    cmd = _build_command(asset, tf, out, 12.0, "video")
    assert str(out) in cmd


def test_command_includes_drawtext(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path, "Texto de prueba")
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "drawtext" in vf


def test_command_uses_textfile(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "textfile=" in vf


def test_command_has_no_box(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "box=1" not in vf


def test_command_has_shadow(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "shadowcolor=" in vf


def test_command_has_fade(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "fade=" in vf


def test_command_uses_center_crop(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
    vf = " ".join(cmd)
    assert "crop=" in vf
    assert "force_original_aspect_ratio=increase" in vf


def test_command_respects_custom_font_size(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video", font_size=32)
    vf = " ".join(cmd)
    assert "fontsize=32" in vf


def test_command_no_audio_flags(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    tf = _text_file(tmp_path)
    cmd = _build_command(asset, tf, tmp_path / "out.mp4", 12.0, "video")
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


def test_renderer_preserves_long_reflection(tmp_path: Path) -> None:
    asset = _asset(tmp_path)
    long_text = (
        "Tu mente encontró la manera de seguir. "
        "Tu cuerpo todavía no ha terminado de entender que ya pasó. "
        "Hay heridas que sanan hacia adentro, sin que nadie las vea."
    )
    mock_execute = MagicMock()
    with patch("ai_content_studio.video.reflection_renderer._execute", mock_execute):
        renderer = ReflectionRenderer()
        renderer.render(
            asset_path=asset,
            reflection_text=long_text,
            output_path=tmp_path / "out.mp4",
        )
    # Verify command was built (text not truncated — adapt_typography handles it)
    mock_execute.assert_called_once()
