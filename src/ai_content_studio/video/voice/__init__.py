"""Voice submodule — TTS provider abstractions."""

from ai_content_studio.video.voice.interface import VoiceProvider
from ai_content_studio.video.voice.kokoro import KokoroProvider

__all__ = ["KokoroProvider", "VoiceProvider"]
