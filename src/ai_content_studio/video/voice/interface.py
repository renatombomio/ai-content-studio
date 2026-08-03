"""Abstract interface for text-to-speech providers."""

from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    """Contract for every TTS backend."""

    @abstractmethod
    def generate(self, text: str) -> bytes:
        """Synthesize narration text and return raw audio bytes."""
