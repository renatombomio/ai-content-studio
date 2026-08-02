"""Abstract interfaces for the Brain module."""

from abc import ABC, abstractmethod

from ai_content_studio.shared.models import Story


class Brain(ABC):
    """Abstract contract for story generation."""

    @abstractmethod
    def generate_story(self, idea: str) -> Story:
        """Generate a structured Story from a creative idea."""
