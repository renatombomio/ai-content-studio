"""FFmpegRenderer — converts a Timeline into a TikTok-ready MP4."""

import subprocess
import tempfile
from pathlib import Path

from ai_content_studio.core.exceptions import RendererError
from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.timeline import Timeline, TimelineScene

_W = 1080
_H = 1920
_SCALE = (
    f"scale={_W}:{_H}:force_original_aspect_ratio=decrease,"
    f"pad={_W}:{_H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
)


class FFmpegRenderer:
    """Renders a Timeline to a single TikTok-compatible MP4 via FFmpeg."""

    def render(self, timeline: Timeline, output_path: Path) -> Path:
        """Render the Timeline to output_path and return it."""
        _validate(timeline)
        with tempfile.TemporaryDirectory() as tmp:
            audio_path: Path | None = None
            if timeline.voice_track is not None:
                audio_path = Path(tmp) / "voice.wav"
                audio_path.write_bytes(timeline.voice_track.audio)
            cmd = _build_command(timeline, output_path, audio_path)
            _execute(cmd)
        return output_path


def _validate(timeline: Timeline) -> None:
    if not timeline.scenes:
        raise RendererError("Timeline has no scenes")
    for ts in timeline.scenes:
        if not ts.assets or all(ta.asset.path is None for ta in ts.assets):
            raise RendererError("Every scene must have at least one asset with a local path")


def _build_command(
    timeline: Timeline, output_path: Path, audio_path: Path | None
) -> list[str]:
    cmd: list[str] = ["ffmpeg", "-y"]
    segments: list[tuple[str, str, float]] = []  # (path, asset_type, duration)

    for ts in timeline.scenes:
        asset = _pick_asset(ts)
        path = asset.path
        assert path is not None  # guaranteed by _validate / _pick_asset
        duration = ts.assets[0].end_time - ts.assets[0].start_time

        if asset.asset_type == "video":
            cmd += ["-i", path]
        else:
            cmd += ["-loop", "1", "-t", str(duration), "-i", path]

        segments.append((path, asset.asset_type, duration))

    if audio_path is not None:
        cmd += ["-i", str(audio_path)]

    n = len(segments)
    filter_parts: list[str] = []
    for i, (_, asset_type, duration) in enumerate(segments):
        if asset_type == "video":
            filter_parts.append(f"[{i}:v]trim=duration={duration},{_SCALE}[v{i}]")
        else:
            filter_parts.append(f"[{i}:v]{_SCALE}[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[outv]")

    cmd += ["-filter_complex", ";".join(filter_parts), "-map", "[outv]"]

    if audio_path is not None:
        cmd += ["-map", f"{n}:a", "-c:a", "aac", "-b:a", "192k"]

    cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p"]
    cmd += ["-movflags", "+faststart", "-t", str(timeline.duration), str(output_path)]

    return cmd


def _pick_asset(ts: TimelineScene) -> Asset:
    for ta in ts.assets:
        if ta.asset.path is not None:
            return ta.asset
    raise RendererError("Scene has no asset with a local path")


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
