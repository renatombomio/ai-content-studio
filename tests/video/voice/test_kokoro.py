"""Tests for KokoroProvider."""

import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ai_content_studio.core.exceptions import ProviderError
from ai_content_studio.video.voice.kokoro import KokoroProvider


def _fake_pipeline_output(audio: "np.ndarray") -> list[tuple[str, str, "np.ndarray"]]:
    return [("text", "phonemes", audio)]


def _mock_pipeline(audio: "np.ndarray | None" = None) -> MagicMock:
    if audio is None:
        audio = np.ones(24000, dtype=np.float32) * 0.1
    mock = MagicMock()
    mock.return_value = iter(_fake_pipeline_output(audio))
    return mock


# --- Return type ---

def test_generate_returns_bytes() -> None:
    with patch("kokoro.KPipeline", return_value=_mock_pipeline()):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        result = provider.generate("Hello world.")
    assert isinstance(result, bytes)


def test_generate_returns_wav_bytes() -> None:
    with patch("kokoro.KPipeline", return_value=_mock_pipeline()):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        result = provider.generate("Hello world.")
    assert result[:4] == b"RIFF"


def test_generate_non_empty_audio() -> None:
    with patch("kokoro.KPipeline", return_value=_mock_pipeline()):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        result = provider.generate("Hello world.")
    assert len(result) > 44  # WAV header is 44 bytes


# --- Text forwarding ---

def test_generate_passes_text_to_pipeline() -> None:
    mock_pipe = _mock_pipeline()
    with patch("kokoro.KPipeline", return_value=mock_pipe):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        provider.generate("A farmer plants a seed.")
    call_kwargs = mock_pipe.call_args
    assert "A farmer plants a seed." in str(call_kwargs)


def test_generate_passes_voice_setting() -> None:
    mock_pipe = _mock_pipeline()
    with patch("kokoro.KPipeline", return_value=mock_pipe):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        provider.generate("narration")
    assert "af_heart" in str(mock_pipe.call_args)


def test_generate_passes_speed_setting() -> None:
    mock_pipe = _mock_pipeline()
    with patch("kokoro.KPipeline", return_value=mock_pipe):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        provider.generate("narration")
    assert "1.0" in str(mock_pipe.call_args)


# --- Pipeline lazy loading ---

def test_pipeline_loaded_on_first_call() -> None:
    with patch("kokoro.KPipeline") as mock_cls:  # type: ignore[attr-defined]
        mock_cls.return_value = _mock_pipeline()
        provider = KokoroProvider()
        assert provider._pipeline is None
        provider.generate("hello")
        assert provider._pipeline is not None


def test_pipeline_not_reloaded_on_second_call() -> None:
    with patch("kokoro.KPipeline") as mock_cls:  # type: ignore[attr-defined]
        mock_cls.return_value = _mock_pipeline()
        provider = KokoroProvider()
        provider.generate("hello")
        provider.generate("world")
        assert mock_cls.call_count == 1


# --- Error handling ---

def test_inference_failure_raises_provider_error() -> None:
    mock_pipe = MagicMock()
    mock_pipe.side_effect = RuntimeError("inference failed")
    with patch("kokoro.KPipeline", return_value=mock_pipe):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        with pytest.raises(ProviderError):
            provider.generate("hello")


def test_pipeline_init_failure_raises_provider_error() -> None:
    with patch("kokoro.KPipeline", side_effect=OSError("espeak not found")):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        with pytest.raises(ProviderError):
            provider.generate("hello")


def test_provider_error_wraps_original_exception() -> None:
    mock_pipe = MagicMock()
    mock_pipe.side_effect = ValueError("bad input")
    with patch("kokoro.KPipeline", return_value=mock_pipe):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        with pytest.raises(ProviderError) as exc_info:
            provider.generate("hello")
    assert exc_info.value.__cause__ is not None


# --- Empty output ---

def test_empty_pipeline_output_returns_bytes() -> None:
    mock_pipe = MagicMock()
    mock_pipe.return_value = iter([])
    with patch("kokoro.KPipeline", return_value=mock_pipe):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        result = provider.generate("")
    assert isinstance(result, bytes)


# --- WAV decoding ---

def test_output_is_readable_wav() -> None:
    with patch("kokoro.KPipeline", return_value=_mock_pipeline()):  # type: ignore[attr-defined]
        provider = KokoroProvider()
        result = provider.generate("test")
    import soundfile as sf  # type: ignore[import-untyped]
    data, sr = sf.read(io.BytesIO(result))
    assert sr == 24000
    assert len(data) > 0
