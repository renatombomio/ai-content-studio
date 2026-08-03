# Official repository: https://github.com/hexgrad/kokoro
# Documentation: https://huggingface.co/hexgrad/Kokoro-82M
# Install: uv add "torch==2.2.2" "kokoro>=0.9.4" soundfile
# Model: hexgrad/Kokoro-82M (82M parameters, Apache 2.0)
# Note: requires espeak-ng system dependency (brew install espeak on macOS)

import io
from typing import Any

import numpy as np
import soundfile as sf  # type: ignore[import-untyped]

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import ProviderError
from ai_content_studio.video.voice.interface import VoiceProvider

_SAMPLE_RATE = 24_000


class KokoroProvider(VoiceProvider):
    """TTS provider backed by Kokoro — local inference, no API key required."""

    def __init__(self) -> None:
        self._pipeline: Any = None

    def generate(self, text: str) -> bytes:
        """Synthesize text and return WAV audio as bytes."""
        settings = get_settings()
        voice: str = settings.kokoro_voice
        speed: float = settings.kokoro_speed
        lang_code = voice[0]

        pipeline = self._get_pipeline(lang_code)
        try:
            chunks = [audio for _, _, audio in pipeline(text, voice=voice, speed=speed)]
        except Exception as exc:
            raise ProviderError(f"Kokoro TTS generation failed: {exc}") from exc

        audio: Any = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
        buf = io.BytesIO()
        sf.write(buf, audio, _SAMPLE_RATE, format="WAV")
        return buf.getvalue()

    def _get_pipeline(self, lang_code: str) -> Any:
        if self._pipeline is None:
            try:
                from kokoro import KPipeline  # type: ignore[import-untyped]
                self._pipeline = KPipeline(lang_code=lang_code)
            except Exception as exc:
                raise ProviderError(f"Kokoro pipeline initialization failed: {exc}") from exc
        return self._pipeline
