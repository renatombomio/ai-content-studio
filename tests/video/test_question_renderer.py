"""Tests for QuestionRenderer."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.video.question_renderer import (
    _Q_MAX_FONT,
    _Q_MAX_TEXT_H,
    _Q_MIN_FONT,
    QuestionRenderer,
    _adapt_question,
)

_QUESTION_DATA = {
    "question_text": "¿Qué parte de ti decidiste esconder para que alguien se quedara?",
    "context": "No siempre lo que guardamos nos protege. A veces protege al otro.",
    "caption": "La pregunta que no te has atrevido a hacerte.",
    "hashtags": ["#shadowwork", "#introspección"],
    "pillar": "shadow_work",
    "generation_date": "2026-08-04",
}


def _question_json(tmp_path: Path) -> Path:
    p = tmp_path / "question.json"
    p.write_text(json.dumps(_QUESTION_DATA), encoding="utf-8")
    return p


# --- adaptive question typography ---

def test_adapt_question_preserves_full_text() -> None:
    text = "¿Qué parte de ti decidiste esconder para que alguien se quedara?"
    wrapped, _, _ = _adapt_question(text)
    for word in text.split():
        assert word in wrapped


def test_adapt_question_fits_within_max_height() -> None:
    text = "¿Qué parte de ti decidiste esconder para que alguien se quedara?"
    wrapped, font_size, line_spacing = _adapt_question(text)
    n = wrapped.count("\n") + 1
    estimated = n * (font_size * 1.3) + max(0, n - 1) * line_spacing
    assert estimated <= _Q_MAX_TEXT_H


def test_adapt_question_returns_max_font_for_short_text() -> None:
    _, font_size, _ = _adapt_question("¿Sí?")
    assert font_size == _Q_MAX_FONT


def test_adapt_question_never_truncates_long_text() -> None:
    long_text = "¿" + " ".join(["palabra"] * 40) + "?"
    wrapped, font_size, _ = _adapt_question(long_text)
    assert font_size >= _Q_MIN_FONT
    for word in long_text.split():
        assert word in wrapped


# --- renderer ---

def test_renderer_raises_if_question_json_missing(tmp_path: Path) -> None:
    renderer = QuestionRenderer()
    with pytest.raises(RendererError, match="question.json not found"):
        renderer.render(
            question_json=tmp_path / "missing.json",
            output_dir=tmp_path,
        )


def test_renderer_returns_cover_and_question_paths(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    with patch("ai_content_studio.video.question_renderer._execute"):
        cover, question = renderer.render(question_json=qj, output_dir=tmp_path)
    assert cover == tmp_path / "cover.png"
    assert question == tmp_path / "question.png"


def test_renderer_calls_ffmpeg_twice(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    mock_execute = MagicMock()
    with patch("ai_content_studio.video.question_renderer._execute", mock_execute):
        renderer.render(question_json=qj, output_dir=tmp_path)
    assert mock_execute.call_count == 2


def test_cover_command_targets_cover_png(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ):
        renderer.render(question_json=qj, output_dir=tmp_path)
    cover_cmd = " ".join(captured[0])
    assert "cover.png" in cover_cmd


def test_question_command_targets_question_png(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ):
        renderer.render(question_json=qj, output_dir=tmp_path)
    question_cmd = " ".join(captured[1])
    assert "question.png" in question_cmd


def test_both_commands_use_ffmpeg(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ):
        renderer.render(question_json=qj, output_dir=tmp_path)
    for cmd in captured:
        assert cmd[0] == "ffmpeg"


def test_question_command_includes_drawtext(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ):
        renderer.render(question_json=qj, output_dir=tmp_path)
    question_cmd = " ".join(captured[1])
    assert "drawtext" in question_cmd


def test_renderer_outputs_single_frame_png(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    renderer = QuestionRenderer()
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ):
        renderer.render(question_json=qj, output_dir=tmp_path)
    for cmd in captured:
        assert "-frames:v" in cmd
        idx = cmd.index("-frames:v")
        assert cmd[idx + 1] == "1"
