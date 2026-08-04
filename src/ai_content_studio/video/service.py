"""RenderService — orchestrates the complete Video Engine pipeline."""

import struct
from pathlib import Path

from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.story import Story
from ai_content_studio.shared.models.timeline import VoiceTrack
from ai_content_studio.video.renderer import FFmpegRenderer
from ai_content_studio.video.subtitles import SubtitleGenerator
from ai_content_studio.video.timeline_builder import TimelineBuilder
from ai_content_studio.video.voice.interface import VoiceProvider

_WAV_HEADER_SIZE = 44


class RenderService:
    """Orchestrates Timeline construction, voice synthesis, subtitle generation, and rendering."""

    def __init__(
        self,
        timeline_builder: TimelineBuilder,
        voice_provider: VoiceProvider | None,
        subtitle_generator: SubtitleGenerator,
        renderer: FFmpegRenderer,
    ) -> None:
        self._timeline_builder = timeline_builder
        self._voice_provider = voice_provider
        self._subtitle_generator = subtitle_generator
        self._renderer = renderer

    def render(
        self,
        story: Story,
        assets_by_scene: dict[str, list[Asset]],
        output_path: Path,
    ) -> Path:
        """Build Timeline, synthesize audio (if provider set), generate subtitles, and render."""
        timeline = self._timeline_builder.build(story, assets_by_scene)

        updates: dict[str, object] = {}

        if self._voice_provider is not None:
            narration = "\n".join(ts.scene.narration for ts in timeline.scenes)
            audio_bytes = self._voice_provider.generate(narration)
            updates["voice_track"] = VoiceTrack(
                audio=audio_bytes,
                sample_rate=_parse_wav_sample_rate(audio_bytes),
                duration=_parse_wav_duration(audio_bytes),
            )

        updates["subtitles"] = self._subtitle_generator.generate(timeline)
        timeline = timeline.model_copy(update=updates)

        return self._renderer.render(timeline, output_path)


def _parse_wav_sample_rate(wav_bytes: bytes) -> int:
    try:
        return int(struct.unpack_from("<I", wav_bytes, 24)[0])
    except struct.error:
        return 0


def _parse_wav_duration(wav_bytes: bytes) -> float:
    try:
        sample_rate = int(struct.unpack_from("<I", wav_bytes, 24)[0])
        num_channels = int(struct.unpack_from("<H", wav_bytes, 22)[0])
        bits_per_sample = int(struct.unpack_from("<H", wav_bytes, 34)[0])
        bytes_per_sample = bits_per_sample // 8
        data_size = len(wav_bytes) - _WAV_HEADER_SIZE
        if sample_rate == 0 or num_channels == 0 or bytes_per_sample == 0 or data_size <= 0:
            return 0.0
        return data_size / (sample_rate * num_channels * bytes_per_sample)
    except struct.error:
        return 0.0
