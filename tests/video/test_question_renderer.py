"""Tests for QuestionRenderer."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.video.question_renderer import (
    _ALL_COVERS,
    _Q_MAX_FONT,
    _Q_MAX_TEXT_H,
    _Q_MIN_FONT,
    QuestionRenderer,
    _adapt_question,
    _empty_history,
    _load_history,
    _save_history,
    _select_cover,
    _validate_assets,
)

_QUESTION_DATA = {
    "question_text": "¿Qué parte de ti decidiste esconder para que alguien se quedara?",
    "context": "No siempre lo que guardamos nos protege. A veces protege al otro.",
    "caption": "La pregunta que no te has atrevido a hacerte.",
    "hashtags": ["#shadowwork", "#introspección"],
    "pillar": "shadow_work",
    "generation_date": "2026-08-05",
}


def _question_json(tmp_path: Path) -> Path:
    p = tmp_path / "question.json"
    p.write_text(json.dumps(_QUESTION_DATA), encoding="utf-8")
    return p


def _full_covers_dir(tmp_path: Path) -> Path:
    covers = tmp_path / "covers"
    covers.mkdir(exist_ok=True)
    for stem in _ALL_COVERS:
        (covers / f"{stem}.png").touch()
    return covers


def _template(tmp_path: Path) -> Path:
    tpl = tmp_path / "question_template.png"
    tpl.touch()
    return tpl


def _history_path(tmp_path: Path) -> Path:
    return tmp_path / "data" / "cover_history.json"


def _renderer(tmp_path: Path) -> QuestionRenderer:
    return QuestionRenderer(
        covers_dir=_full_covers_dir(tmp_path),
        question_template=_template(tmp_path),
        history_path=_history_path(tmp_path),
    )


# --- adaptive typography ---

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


# --- history persistence ---

def test_load_history_creates_file_if_missing(tmp_path: Path) -> None:
    hp = tmp_path / "data" / "cover_history.json"
    assert not hp.exists()
    h = _load_history(hp)
    assert hp.exists()
    assert set(h["usage"].keys()) == set(_ALL_COVERS)
    assert h["episodes"] == {}


def test_load_history_initialises_all_covers_to_zero(tmp_path: Path) -> None:
    hp = tmp_path / "cover_history.json"
    h = _load_history(hp)
    assert all(v == 0 for v in h["usage"].values())


def test_load_history_preserves_existing_counts(tmp_path: Path) -> None:
    hp = tmp_path / "cover_history.json"
    initial = _empty_history()
    initial["usage"]["03_writing"] = 5
    _save_history(initial, hp)
    h = _load_history(hp)
    assert h["usage"]["03_writing"] == 5


def test_load_history_raises_on_malformed_json(tmp_path: Path) -> None:
    hp = tmp_path / "cover_history.json"
    hp.write_text("not json", encoding="utf-8")
    with pytest.raises(RendererError, match="unreadable"):
        _load_history(hp)


def test_save_history_creates_parent_dirs(tmp_path: Path) -> None:
    hp = tmp_path / "deep" / "nested" / "cover_history.json"
    _save_history(_empty_history(), hp)
    assert hp.exists()


def test_save_and_reload_roundtrip(tmp_path: Path) -> None:
    hp = tmp_path / "cover_history.json"
    h = _empty_history()
    h["usage"]["07_reflecting"] = 3
    h["episodes"]["batch_001_question_001"] = "07_reflecting"
    _save_history(h, hp)
    loaded = _load_history(hp)
    assert loaded["usage"]["07_reflecting"] == 3
    assert loaded["episodes"]["batch_001_question_001"] == "07_reflecting"


# --- cover selection ---

def test_select_cover_picks_from_pillar_pool(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    history = _empty_history()
    result = _select_cover(EditorialPillar.SHADOW_WORK, covers, history)
    assert result in {"05_pointing", "01_holding_mug", "06_tired"}


def test_select_cover_picks_least_used(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    history = _empty_history()
    history["usage"]["05_pointing"] = 5
    history["usage"]["01_holding_mug"] = 5
    history["usage"]["06_tired"] = 1
    result = _select_cover(EditorialPillar.SHADOW_WORK, covers, history)
    assert result == "06_tired"


def test_select_cover_breaks_ties_randomly(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    history = _empty_history()
    # all at 0 — any pool member is valid
    results = {_select_cover(EditorialPillar.SHADOW_WORK, covers, history) for _ in range(30)}
    assert results <= {"05_pointing", "01_holding_mug", "06_tired"}
    assert len(results) > 1  # randomness confirmed


def test_select_cover_all_pillars_resolve(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    history = _empty_history()
    for pillar in EditorialPillar:
        result = _select_cover(pillar, covers, history)
        assert result in _ALL_COVERS


# --- asset validation ---

def test_validate_assets_passes_when_all_present(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    tpl = _template(tmp_path)
    hp = _history_path(tmp_path)
    _validate_assets(covers, tpl, hp)  # must not raise


def test_validate_assets_raises_when_cover_missing(tmp_path: Path) -> None:
    covers = tmp_path / "covers"
    covers.mkdir()
    for stem in _ALL_COVERS[:-1]:
        (covers / f"{stem}.png").touch()
    tpl = _template(tmp_path)
    hp = _history_path(tmp_path)
    with pytest.raises(RendererError, match="Missing production assets"):
        _validate_assets(covers, tpl, hp)


def test_validate_assets_raises_when_template_missing(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    hp = _history_path(tmp_path)
    with pytest.raises(RendererError, match="Missing production assets"):
        _validate_assets(covers, tmp_path / "nonexistent_template.png", hp)


def test_validate_assets_raises_when_history_malformed(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    tpl = _template(tmp_path)
    hp = _history_path(tmp_path)
    hp.parent.mkdir(parents=True, exist_ok=True)
    hp.write_text("not json", encoding="utf-8")
    with pytest.raises(RendererError, match="unreadable"):
        _validate_assets(covers, tpl, hp)


def test_validate_assets_passes_when_history_absent(tmp_path: Path) -> None:
    covers = _full_covers_dir(tmp_path)
    tpl = _template(tmp_path)
    hp = _history_path(tmp_path)
    assert not hp.exists()
    _validate_assets(covers, tpl, hp)  # absent → auto-create; must not raise


def test_validate_assets_error_names_missing_files(tmp_path: Path) -> None:
    covers = tmp_path / "covers"
    covers.mkdir()
    hp = _history_path(tmp_path)
    with pytest.raises(RendererError) as exc_info:
        _validate_assets(covers, tmp_path / "nonexistent_template.png", hp)
    msg = str(exc_info.value)
    assert "question_template.png" in msg
    assert "01_holding_mug" in msg


# --- renderer ---

def test_renderer_raises_if_question_json_missing(tmp_path: Path) -> None:
    r = _renderer(tmp_path)
    with pytest.raises(RendererError, match="question.json not found"):
        r.render(question_json=tmp_path / "missing.json", output_dir=tmp_path)


def test_renderer_raises_if_assets_missing(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    r = QuestionRenderer(
        covers_dir=tmp_path / "empty_covers",
        question_template=tmp_path / "nonexistent.png",
        history_path=_history_path(tmp_path),
    )
    with pytest.raises(RendererError, match="Missing production assets"):
        r.render(question_json=qj, output_dir=tmp_path)


def test_renderer_returns_cover_and_question_paths(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    r = _renderer(tmp_path)
    with patch("ai_content_studio.video.question_renderer._execute"), \
         patch("shutil.copy2"):
        cover, question = r.render(question_json=qj, output_dir=tmp_path / "out")
    assert cover == tmp_path / "out" / "cover.png"
    assert question == tmp_path / "out" / "question.png"


def test_renderer_copies_cover_not_generates(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    r = _renderer(tmp_path)
    mock_execute = MagicMock()
    with patch("ai_content_studio.video.question_renderer._execute", mock_execute), \
         patch("shutil.copy2") as mock_copy:
        r.render(question_json=qj, output_dir=tmp_path / "out")
    mock_copy.assert_called_once()
    all_cmd_str = " ".join(str(a) for call in mock_execute.call_args_list for a in call.args[0])
    assert "cover.png" not in all_cmd_str


def test_renderer_calls_ffmpeg_once_for_question(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    r = _renderer(tmp_path)
    mock_execute = MagicMock()
    with patch("ai_content_studio.video.question_renderer._execute", mock_execute), \
         patch("shutil.copy2"):
        r.render(question_json=qj, output_dir=tmp_path / "out")
    assert mock_execute.call_count == 1


def test_renderer_updates_history_after_render(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    hp = _history_path(tmp_path)
    r = _renderer(tmp_path)
    with patch("ai_content_studio.video.question_renderer._execute"), \
         patch("shutil.copy2"):
        r.render(question_json=qj, output_dir=tmp_path / "out")
    history = _load_history(hp)
    total_used = sum(history["usage"].values())
    assert total_used == 1
    assert len(history["episodes"]) == 1


def test_renderer_increments_cover_count_across_runs(tmp_path: Path) -> None:
    hp = _history_path(tmp_path)
    r = _renderer(tmp_path)
    with patch("ai_content_studio.video.question_renderer._execute"), \
         patch("shutil.copy2"):
        for i in range(3):
            out = tmp_path / f"out_{i}"
            out.mkdir()
            r.render(question_json=_question_json(tmp_path), output_dir=out)
    history = _load_history(hp)
    assert sum(history["usage"].values()) == 3


def test_renderer_selects_least_used_cover(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    hp = _history_path(tmp_path)
    # Pre-load history with all shadow_work pool covers at high count except one
    h = _empty_history()
    h["usage"]["05_pointing"] = 10
    h["usage"]["01_holding_mug"] = 10
    h["usage"]["06_tired"] = 1
    _save_history(h, hp)
    r = _renderer(tmp_path)
    with patch("ai_content_studio.video.question_renderer._execute"), \
         patch("shutil.copy2") as mock_copy:
        r.render(question_json=qj, output_dir=tmp_path / "out")
    copied_src = str(mock_copy.call_args.args[0])
    assert "06_tired" in copied_src


def test_renderer_stores_episode_in_history(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    hp = _history_path(tmp_path)
    out = tmp_path / "batch_003" / "question_001"
    out.mkdir(parents=True)
    r = _renderer(tmp_path)
    with patch("ai_content_studio.video.question_renderer._execute"), \
         patch("shutil.copy2"):
        r.render(question_json=qj, output_dir=out)
    history = _load_history(hp)
    assert "batch_003_question_001" in history["episodes"]


def test_question_command_uses_template_as_input(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    r = _renderer(tmp_path)
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ), patch("shutil.copy2"):
        r.render(question_json=qj, output_dir=tmp_path / "out")
    assert str(r._question_template) in " ".join(captured[0])


def test_question_command_outputs_single_frame(tmp_path: Path) -> None:
    qj = _question_json(tmp_path)
    r = _renderer(tmp_path)
    captured: list[list[str]] = []
    with patch(
        "ai_content_studio.video.question_renderer._execute",
        side_effect=lambda cmd: captured.append(cmd),
    ), patch("shutil.copy2"):
        r.render(question_json=qj, output_dir=tmp_path / "out")
    cmd = captured[0]
    assert "-frames:v" in cmd
    assert cmd[cmd.index("-frames:v") + 1] == "1"
