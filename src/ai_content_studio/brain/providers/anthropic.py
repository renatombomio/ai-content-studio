"""Anthropic LLM provider implementation."""

import anthropic as anthropic_sdk

from ai_content_studio.brain.providers.base import LLMProvider
from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import ProviderError


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.anthropic_model
        self._client = anthropic_sdk.Anthropic(api_key=settings.anthropic_api_key)

    def generate(self, prompt: str) -> str:
        """Send a prompt to Anthropic and return the generated text."""
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return str(message.content[0].text)  # type: ignore[union-attr]
        except anthropic_sdk.APIError as exc:
            raise ProviderError(f"Anthropic API error: {exc}") from exc
