"""QuestionRenderer — renders the two-slide PNG carousel for a Cocoa Question."""

import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

from ai_content_studio.core.exceptions import RendererError

# Brand palette (BRAND.md)
_BG = "0x1C0F07"
_CREAM = "0xE8D9B5"
_CREAM_DIM = "0xE8D9B5@0.65"
_TEAL = "0x2E6B5E"

_W = 1080
_H = 1920

_COCO_PATH = Path("/Users/renato/Downloads/ChatGPT Image 4 ago 2026, 00_16_37.png")

_SCALE_CROP = (
    f"scale={_W}:{_H}:force_original_aspect_ratio=increase:flags=lanczos,"
    f"crop={_W}:{_H},setsar=1"
)

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

# Adaptive question typography bounds
_Q_MAX_FONT = 52
_Q_MIN_FONT = 30
_Q_FONT_STEP = 2
_Q_LINE_HEIGHT_RATIO = 1.3
_Q_CHAR_WIDTH_RATIO = 0.55
_Q_TEXT_WIDTH_RATIO = 0.80
_Q_CENTER_RATIO = 0.42
_Q_MAX_TEXT_H = int(_H * 0.38)

# Context text
_C_FONT = 34
_C_GAP = 60


def _find_font() -> str | None:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _escape_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")


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


def _wrap_context(text: str) -> str:
    char_width = _C_FONT * _Q_CHAR_WIDTH_RATIO
    line_width = max(20, int(_W * _Q_TEXT_WIDTH_RATIO / char_width))
    return "\n".join(textwrap.wrap(text, width=line_width))


def _text_block_height(wrapped: str, font_size: int, line_spacing: int) -> int:
    n = wrapped.count("\n") + 1
    return int(n * font_size * _Q_LINE_HEIGHT_RATIO + max(0, n - 1) * line_spacing)


class QuestionRenderer:
    """Renders a Cocoa Question into two editorial PNG slides."""

    def render(self, question_json: Path, output_dir: Path) -> tuple[Path, Path]:
        """Render cover.png and question.png into output_dir."""
        if not question_json.exists():
            raise RendererError(f"question.json not found: {question_json}")

        data = json.loads(question_json.read_text(encoding="utf-8"))
        question_text = data["question_text"]
        context = data.get("context", "")

        font = _find_font()
        cover = output_dir / "cover.png"
        question_slide = output_dir / "question.png"

        _render_cover(cover, font)
        _render_question(question_text, context, question_slide, font)

        return cover, question_slide


def _render_cover(output: Path, font: str | None) -> None:
    font_arg = f"fontfile={font}:" if font else ""
    coco_exists = _COCO_PATH.exists()

    brand_text = (
        f"drawbox=x=0:y=0:w=8:h={_H}:color={_TEAL}:t=fill,"
        f"drawtext={font_arg}text='Cocoa Talk':fontsize=88:fontcolor={_CREAM}:"
        f"x=(w-text_w)/2:y=130:shadowcolor=black@0.6:shadowx=3:shadowy=3,"
        f"drawbox=x=180:y=258:w=720:h=2:color={_TEAL}@0.8:t=fill,"
        f"drawtext={font_arg}text='Pregunta de la Semana':fontsize=40:"
        f"fontcolor={_CREAM}@0.75:x=(w-text_w)/2:y=278:"
        f"shadowcolor=black@0.5:shadowx=1:shadowy=1"
    )

    if coco_exists:
        vf = f"{_SCALE_CROP},eq=brightness=-0.40:saturation=0.65,{brand_text}"
        cmd = ["ffmpeg", "-y", "-i", str(_COCO_PATH), "-vf", vf, "-frames:v", "1", str(output)]
    else:
        vf = brand_text
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={_BG}:size={_W}x{_H}:r=1",
            "-vf", vf,
            "-frames:v", "1", str(output),
        ]

    _execute(cmd)


def _render_question(
    question_text: str,
    context: str,
    output: Path,
    font: str | None,
) -> None:
    font_arg = f"fontfile={font}:" if font else ""

    q_wrapped, q_font, q_spacing = _adapt_question(question_text)
    q_h = _text_block_height(q_wrapped, q_font, q_spacing)
    q_y = max(80, int(_H * _Q_CENTER_RATIO - q_h / 2))

    c_wrapped = _wrap_context(context) if context else ""
    c_y = q_y + q_h + _C_GAP

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(q_wrapped)
        q_file = Path(f.name)

    filters = (
        f"drawtext={font_arg}"
        f"textfile={_escape_path(q_file)}:"
        f"fontsize={q_font}:"
        f"fontcolor={_CREAM}:"
        f"x=(w-text_w)/2:"
        f"y={q_y}:"
        f"shadowcolor=black@0.5:"
        f"shadowx=2:"
        f"shadowy=2:"
        f"line_spacing={q_spacing}"
    )

    c_file: Path | None = None
    if c_wrapped:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(c_wrapped)
            c_file = Path(f.name)

        filters += (
            f",drawtext={font_arg}"
            f"textfile={_escape_path(c_file)}:"
            f"fontsize={_C_FONT}:"
            f"fontcolor={_CREAM_DIM}:"
            f"x=(w-text_w)/2:"
            f"y={c_y}:"
            f"shadowcolor=black@0.4:"
            f"shadowx=1:"
            f"shadowy=1:"
            f"line_spacing=8"
        )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={_BG}:size={_W}x{_H}:r=1",
        "-vf", filters,
        "-frames:v", "1", str(output),
    ]

    try:
        _execute(cmd)
    finally:
        q_file.unlink(missing_ok=True)
        if c_file:
            c_file.unlink(missing_ok=True)


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
