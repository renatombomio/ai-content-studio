"""Tests for LLMProvider abstract interface."""

import inspect

import pytest

from ai_content_studio.brain.providers import LLMProvider


def test_llm_provider_is_abstract() -> None:
    assert inspect.isabstract(LLMProvider)


def test_llm_provider_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_generate_is_abstract_method() -> None:
    assert getattr(LLMProvider.generate, "__isabstractmethod__", False)


def test_subclass_must_implement_generate() -> None:
    class IncompleteProvider(LLMProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()  # type: ignore[abstract]


def test_concrete_subclass_can_be_instantiated() -> None:
    class StubProvider(LLMProvider):
        def generate(self, prompt: str) -> str:
            return "stub response"

    provider = StubProvider()
    assert provider.generate("test") == "stub response"
