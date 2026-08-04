"""QuestionRenderer — renders the two-slide PNG carousel for a Cocoa Question."""

import json
import random
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.shared.models.editorial import EditorialPillar

_ASSETS_ROOT = Path(__file__).parents[3] / "assets"
_COVERS_DIR = _ASSETS_ROOT / "covers"
_QUESTION_TEMPLATE = _ASSETS_ROOT / "question" / "question_template.png"
_DATA_DIR = Path(__file__).parents[3] / "data"
_COVER_HISTORY_PATH = _DATA_DIR / "cover_history.json"

_W = 1080
_H = 1920

# Approved cover stems — exact filenames (without extension).
# Emotion reference:
#   01_holding_mug  → calm, vulnerability, emotional honesty, quiet reflection
#   02_thinking     → existential questions, purpose, meaning, overthinking
#   03_writing      → healing, journaling, personal growth, learning
#   04_listening    → empathy, relationships, communication, understanding
#   05_pointing     → uncomfortable truths, direct challenges, accountability
#   06_tired        → burnout, anxiety, stress, emotional exhaustion
#   07_reflecting   → identity, life decisions, introspection, self-discovery
#   08_applauding   → confidence, progress, celebrating growth, self-worth
_ALL_COVERS = [
    "01_holding_mug",
    "02_thinking",
    "03_writing",
    "04_listening",
    "05_pointing",
    "06_tired",
    "07_reflecting",
    "08_applauding",
]

_COVER_MAP: dict[EditorialPillar, list[str]] = {
    EditorialPillar.SHADOW_WORK: [
        "05_pointing",
        "01_holding_mug",
        "06_tired",
    ],
    EditorialPillar.INTRAPERSONAL: [
        "07_reflecting",
        "02_thinking",
        "08_applauding",
    ],
    EditorialPillar.MENTAL_HEALTH: [
        "06_tired",
        "01_holding_mug",
        "04_listening",
    ],
    EditorialPillar.POETIC_WRITING: [
        "07_reflecting",
        "03_writing",
        "02_thinking",
    ],
}

_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Times New Roman.ttf",
    "/System/Library/Fonts/Times.ttc",
    "/System/Library/Fonts/Palatino.ttc",
    "/Library/Fonts/Arial Unicode MS.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

_TEXT_COLOR = "0xF5DFA0"

_Q_MAX_FONT = 72
_Q_MIN_FONT = 36
_Q_FONT_STEP = 2
_Q_LINE_HEIGHT_RATIO = 1.3
_Q_CHAR_WIDTH_RATIO = 0.55
_Q_TEXT_WIDTH_RATIO = 0.78

_TEMPLATE_TEXT_Y_CENTER = 820
_TEMPLATE_TEXT_Y_MIN = 480
_TEMPLATE_TEXT_Y_MAX = 1300
_Q_MAX_TEXT_H = _TEMPLATE_TEXT_Y_MAX - _TEMPLATE_TEXT_Y_MIN


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _find_font() -> str | None:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _escape_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

def _adapt_question(text: str) -> tuple[str, int, int]:
    """Return (wrapped, font_size, line_spacing) fitting within _Q_MAX_TEXT_H."""
    for font_size in range(_Q_MAX_FONT, _Q_MIN_FONT - 1, -_Q_FONT_STEP):
        char_width = font_size * _Q_CHAR_WIDTH_RATIO
        line_width = max(16, int(_W * _Q_TEXT_WIDTH_RATIO / char_width))
        line_spacing = max(6, int(font_size * 0.25))
        lines = textwrap.wrap(text, width=line_width)
        n = len(lines)
        estimated = n * (font_size * _Q_LINE_HEIGHT_RATIO) + max(0, n - 1) * line_spacing
        if estimated <= _Q_MAX_TEXT_H:
            return "\n".join(lines), font_size, line_spacing
    char_width = _Q_MIN_FONT * _Q_CHAR_WIDTH_RATIO
    line_width = max(16, int(_W * _Q_TEXT_WIDTH_RATIO / char_width))
    lines = textwrap.wrap(text, width=line_width)
    return "\n".join(lines), _Q_MIN_FONT, 6


def _text_block_height(wrapped: str, font_size: int, line_spacing: int) -> int:
    n = wrapped.count("\n") + 1
    return int(n * font_size * _Q_LINE_HEIGHT_RATIO + max(0, n - 1) * line_spacing)


# ---------------------------------------------------------------------------
# Cover history
# ---------------------------------------------------------------------------

def _empty_history() -> dict[str, Any]:
    return {
        "usage": {stem: 0 for stem in _ALL_COVERS},
        "episodes": {},
    }


def _load_history(path: Path) -> dict[str, Any]:
    """Load cover_history.json, creating it if absent."""
    if not path.exists():
        history: dict[str, Any] = _empty_history()
        _save_history(history, path)
        return history
    try:
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RendererError(f"cover_history.json unreadable: {exc}") from exc
    usage = raw.get("usage", {})
    for stem in _ALL_COVERS:
        usage.setdefault(stem, 0)
    raw["usage"] = usage
    raw.setdefault("episodes", {})
    return raw


def _save_history(history: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Asset validation
# ---------------------------------------------------------------------------

def _resolve_cover(stem: str, covers_dir: Path) -> Path | None:
    for ext in ("png", "jpg", "jpeg"):
        p = covers_dir / f"{stem}.{ext}"
        if p.exists():
            return p
    return None


def _validate_assets(covers_dir: Path, template: Path, history_path: Path) -> None:
    """Raise RendererError listing every missing or unreadable production asset."""
    missing: list[str] = []
    for stem in _ALL_COVERS:
        if _resolve_cover(stem, covers_dir) is None:
            missing.append(f"assets/covers/{stem}.png")
    if not template.exists():
        missing.append("assets/question/question_template.png")
    if missing:
        lines = "\n".join(f"  • {m}" for m in missing)
        raise RendererError(f"Missing production assets — generation stopped:\n{lines}")
    if history_path.exists():
        try:
            json.loads(history_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RendererError(f"cover_history.json unreadable: {exc}") from exc


# ---------------------------------------------------------------------------
# Cover selection
# ---------------------------------------------------------------------------

def _select_cover(
    pillar: EditorialPillar,
    covers_dir: Path,
    history: dict[str, Any],
) -> str:
    """Return the stem of the least-used cover in the pillar pool."""
    pool = _COVER_MAP.get(pillar, _ALL_COVERS)
    available = [stem for stem in pool if _resolve_cover(stem, covers_dir) is not None]
    if not available:
        available = [stem for stem in _ALL_COVERS if _resolve_cover(stem, covers_dir) is not None]
    usage: dict[str, Any] = history["usage"]
    min_count = min(usage.get(stem, 0) for stem in available)
    candidates = [stem for stem in available if usage.get(stem, 0) == min_count]
    return random.choice(candidates)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class QuestionRenderer:
    """Renders a Cocoa Question into two editorial PNG slides."""

    def __init__(
        self,
        covers_dir: Path | None = None,
        question_template: Path | None = None,
        history_path: Path | None = None,
    ) -> None:
        self._covers_dir = covers_dir or _COVERS_DIR
        self._question_template = question_template or _QUESTION_TEMPLATE
        self._history_path = history_path or _COVER_HISTORY_PATH

    def render(self, question_json: Path, output_dir: Path) -> tuple[Path, Path]:
        """Render cover.png and question.png into output_dir."""
        if not question_json.exists():
            raise RendererError(f"question.json not found: {question_json}")

        _validate_assets(self._covers_dir, self._question_template, self._history_path)

        data = json.loads(question_json.read_text(encoding="utf-8"))
        question_text = data["question_text"]
        pillar_raw = data.get("pillar", EditorialPillar.SHADOW_WORK.value)
        try:
            pillar = EditorialPillar(pillar_raw)
        except ValueError:
            pillar = EditorialPillar.SHADOW_WORK

        episode_id = f"{output_dir.parent.name}_{output_dir.name}"

        history = _load_history(self._history_path)
        selected_stem = _select_cover(pillar, self._covers_dir, history)
        src = _resolve_cover(selected_stem, self._covers_dir)
        if src is None:
            raise RendererError(f"Cover asset not found: {selected_stem}")

        cover = output_dir / "cover.png"
        question_slide = output_dir / "question.png"

        shutil.copy2(src, cover)

        history["usage"][selected_stem] = history["usage"].get(selected_stem, 0) + 1
        history["episodes"][episode_id] = selected_stem
        _save_history(history, self._history_path)

        _render_question(question_text, question_slide, self._question_template)

        return cover, question_slide


# ---------------------------------------------------------------------------
# Question slide rendering
# ---------------------------------------------------------------------------

def _render_question(question_text: str, output: Path, template: Path) -> None:
    font = _find_font()
    font_arg = f"fontfile={font}:" if font else ""

    q_wrapped, q_font, q_spacing = _adapt_question(question_text)
    q_h = _text_block_height(q_wrapped, q_font, q_spacing)

    q_y = max(_TEMPLATE_TEXT_Y_MIN, _TEMPLATE_TEXT_Y_CENTER - q_h // 2)
    if q_y + q_h > _TEMPLATE_TEXT_Y_MAX:
        q_y = max(_TEMPLATE_TEXT_Y_MIN, _TEMPLATE_TEXT_Y_MAX - q_h)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(q_wrapped)
        q_file = Path(f.name)

    filters = (
        f"scale={_W}:{_H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={_W}:{_H},setsar=1,"
        f"drawtext={font_arg}"
        f"textfile={_escape_path(q_file)}:"
        f"fontsize={q_font}:"
        f"fontcolor={_TEXT_COLOR}:"
        f"x=(w-text_w)/2:"
        f"y={q_y}:"
        f"shadowcolor=black@0.5:"
        f"shadowx=2:"
        f"shadowy=2:"
        f"line_spacing={q_spacing}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(template),
        "-vf", filters,
        "-frames:v", "1", str(output),
    ]

    try:
        _execute(cmd)
    finally:
        q_file.unlink(missing_ok=True)


def _execute(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode(errors="replace")
        raise RendererError(f"FFmpeg failed (exit {exc.returncode}): {stderr}") from exc
    except FileNotFoundError as exc:
        raise RendererError("FFmpeg not found — ensure it is installed and on PATH") from exc
    except OSError as exc:
        raise RendererError(f"FFmpeg execution failed: {exc}") from exc
