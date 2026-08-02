"""Tests for AnthropicProvider."""

from unittest.mock import MagicMock, patch

import anthropic as anthropic_sdk
import pytest

from ai_content_studio.brain.providers.anthropic import AnthropicProvider
from ai_content_studio.core.exceptions import ProviderError


def _make_provider() -> AnthropicProvider:
    with patch("ai_content_studio.brain.providers.anthropic.anthropic_sdk.Anthropic"):
        return AnthropicProvider()


def _mock_response(text: str) -> MagicMock:
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


def test_generate_sends_prompt_to_anthropic() -> None:
    with patch("ai_content_studio.brain.providers.anthropic.anthropic_sdk.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_response("result text")

        provider = AnthropicProvider()
        provider.generate("test prompt")

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args
        assert "test prompt" in str(call_kwargs)


def test_generate_returns_text() -> None:
    with patch("ai_content_studio.brain.providers.anthropic.anthropic_sdk.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_response("generated story")

        provider = AnthropicProvider()
        result = provider.generate("a prompt")

        assert result == "generated story"


def test_sdk_exception_raises_provider_error() -> None:
    with patch("ai_content_studio.brain.providers.anthropic.anthropic_sdk.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic_sdk.APIStatusError(
            message="rate limit",
            response=MagicMock(status_code=429),
            body={},
        )

        provider = AnthropicProvider()
        with pytest.raises(ProviderError):
            provider.generate("a prompt")


def test_provider_uses_model_from_settings() -> None:
    with patch("ai_content_studio.brain.providers.anthropic.anthropic_sdk.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_response("ok")

        provider = AnthropicProvider()
        provider.generate("prompt")

        call_kwargs = mock_client.messages.create.call_args
        assert "claude-sonnet-4" in str(call_kwargs)
