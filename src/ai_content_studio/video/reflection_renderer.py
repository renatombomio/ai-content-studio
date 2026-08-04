"""ReflectionRenderer — renders a single-asset short editorial reflection video."""

import subprocess
import tempfile
import textwrap
from pathlib import Path

from ai_content_studio.core.exceptions import RendererError

RENDERER_VERSION = "2.0.0"

_W = 1080
_H = 1920
_DEFAULT_DURATION = 12.0
_TEXT_COLOR = "white"
_SHADOW_COLOR = "black@0.65"
_SHADOW_OFFSET = 3
_TEXT_Y_CENTER = 0.45
_FADE_DURATION = 0.3

# Adaptive typography bounds
_MAX_FONT_SIZE = 42
_MIN_FONT_SIZE = 26
_FONT_SIZE_STEP = 2
_LINE_HEIGHT_RATIO = 1.25
_CHAR_WIDTH_RATIO = 0.55
_TEXT_WIDTH_RATIO = 0.80
_MAX_TEXT_HEIGHT = int(_H * 0.40)  # 768 px — 40% of frame

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


def _find_font() -> str | None:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _wrap_text(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _adapt_typography(text: str) -> tuple[str, int, int]:
    """Return (wrapped_text, font_size, line_spacing) fitting within _MAX_TEXT_HEIGHT.

    Progressively reduces font size until the estimated text block height
    fits within 40% of the frame. The full text is always preserved.
    """
    for font_size in range(_MAX_FONT_SIZE, _MIN_FONT_SIZE - 1, -_FONT_SIZE_STEP):
        char_width = font_size * _CHAR_WIDTH_RATIO
        line_width = max(20, int(_W * _TEXT_WIDTH_RATIO / char_width))
        line_spacing = max(6, int(font_size * 0.28))

        lines = textwrap.wrap(text, width=line_width)
        n = len(lines)
        estimated_height = n * (font_size * _LINE_HEIGHT_RATIO) + max(0, n - 1) * line_spacing

        if estimated_height <= _MAX_TEXT_HEIGHT:
            return "\n".join(lines), font_size, line_spacing

    # Minimum-size fallback — never truncates, just renders small
    char_width = _MIN_FONT_SIZE * _CHAR_WIDTH_RATIO
    line_width = max(20, int(_W * _TEXT_WIDTH_RATIO / char_width))
    line_spacing = 6
    return "\n".join(textwrap.wrap(text, width=line_width)), _MIN_FONT_SIZE, line_spacing


def _escape_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")


class ReflectionRenderer:
    """Renders a short editorial reflection as a vertical looping video with typography."""

    def render(
        self,
        asset_path: Path,
        reflection_text: str,
        output_path: Path,
        duration: float = _DEFAULT_DURATION,
        asset_type: str = "video",
    ) -> Path:
        if not asset_path.exists():
            raise RendererError(f"Asset not found: {asset_path}")

        wrapped, font_size, line_spacing = _adapt_typography(reflection_text)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(wrapped)
            text_file = Path(f.name)

        try:
            cmd = _build_command(
                asset_path, text_file, output_path, duration, asset_type,
                font_size, line_spacing,
            )
            _execute(cmd)
        finally:
            text_file.unlink(missing_ok=True)

        return output_path


def _build_command(
    asset_path: Path,
    text_file: Path,
    output_path: Path,
    duration: float,
    asset_type: str,
    font_size: int = _MAX_FONT_SIZE,
    line_spacing: int = 14,
) -> list[str]:
    cmd: list[str] = ["ffmpeg", "-y"]

    if asset_type == "video":
        cmd += ["-stream_loop", "-1", "-i", str(asset_path)]
    else:
        cmd += ["-loop", "1", "-i", str(asset_path)]

    font = _find_font()
    font_arg = f"fontfile={font}:" if font else ""
    text_arg = f"textfile={_escape_path(text_file)}"

    drawtext = (
        f"drawtext={font_arg}"
        f"{text_arg}:"
        f"fontsize={font_size}:"
        f"fontcolor={_TEXT_COLOR}:"
        f"x=(w-text_w)/2:"
        f"y=h*{_TEXT_Y_CENTER}-text_h/2:"
        f"shadowcolor={_SHADOW_COLOR}:"
        f"shadowx={_SHADOW_OFFSET}:"
        f"shadowy={_SHADOW_OFFSET}:"
        f"line_spacing={line_spacing}"
    )

    fade = f"fade=type=in:start_time=0:duration={_FADE_DURATION}"
    vf = f"{_SCALE_CROP},{drawtext},{fade}"

    cmd += [
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]

    return cmd


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
