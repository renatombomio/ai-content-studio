"""Tests for VoiceProvider interface."""

import pytest

from ai_content_studio.video.voice.interface import VoiceProvider


def test_voice_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        VoiceProvider()  # type: ignore[abstract]


def test_generate_must_be_implemented() -> None:
    class Incomplete(VoiceProvider):
        pass

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_concrete_subclass_instantiates() -> None:
    class FakeProvider(VoiceProvider):
        def generate(self, text: str) -> bytes:
            return b"audio"

    provider = FakeProvider()
    assert isinstance(provider, VoiceProvider)


def test_generate_returns_bytes() -> None:
    class FakeProvider(VoiceProvider):
        def generate(self, text: str) -> bytes:
            return text.encode()

    result = FakeProvider().generate("hello")
    assert isinstance(result, bytes)


def test_generate_receives_text() -> None:
    class FakeProvider(VoiceProvider):
        def generate(self, text: str) -> bytes:
            self.last = text
            return b""

    p = FakeProvider()
    p.generate("narration text")
    assert p.last == "narration text"
