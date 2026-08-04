"""ReflectionRenderer — renders a single-asset short editorial reflection video."""

import subprocess
import textwrap
from pathlib import Path

from ai_content_studio.core.exceptions import RendererError

_W = 1080
_H = 1920
_DEFAULT_DURATION = 12.0
_FONT_SIZE = 52
_LINE_WIDTH = 28  # characters per line for reflection text
_TEXT_COLOR = "white"
_BOX_COLOR = "black@0.45"
_BOX_BORDER = 30

_SCALE = (
    f"scale={_W}:{_H}:force_original_aspect_ratio=decrease,"
    f"pad={_W}:{_H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
)

_FONT_CANDIDATES = [
    "/Library/Fonts/Arial Unicode MS.ttf",
    "/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _find_font() -> str | None:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _wrap_text(text: str, width: int = _LINE_WIDTH) -> str:
    lines = textwrap.wrap(text, width=width)
    # FFmpeg drawtext uses \n for newlines in textfile; literal \n in filter escaping is complex.
    # We write to a temp textfile instead — this returns the wrapped content for the file.
    return "\n".join(lines)


def _escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter value."""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")


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
        """Render a single asset with reflection text overlay to output_path."""
        if not asset_path.exists():
            raise RendererError(f"Asset not found: {asset_path}")

        wrapped = _wrap_text(reflection_text)
        cmd = _build_command(asset_path, wrapped, output_path, duration, asset_type)
        _execute(cmd)
        return output_path


def _build_command(
    asset_path: Path,
    wrapped_text: str,
    output_path: Path,
    duration: float,
    asset_type: str,
) -> list[str]:
    cmd: list[str] = ["ffmpeg", "-y"]

    if asset_type == "video":
        cmd += ["-stream_loop", "-1", "-i", str(asset_path)]
    else:
        cmd += ["-loop", "1", "-i", str(asset_path)]

    font = _find_font()
    font_arg = f"fontfile={font}:" if font else ""

    escaped = _escape_drawtext(wrapped_text)
    drawtext = (
        f"drawtext={font_arg}"
        f"text='{escaped}':"
        f"fontsize={_FONT_SIZE}:"
        f"fontcolor={_TEXT_COLOR}:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2:"
        f"box=1:"
        f"boxcolor={_BOX_COLOR}:"
        f"boxborderw={_BOX_BORDER}:"
        f"line_spacing=10"
    )

    vf = f"{_SCALE},{drawtext}"

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
