"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract contract for any language model provider."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send a prompt and return the raw text response."""
