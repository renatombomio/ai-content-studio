"""B-003 — Real Kokoro Integration bring-up.

Reads output/story.json, synthesizes narration for all scenes via KokoroProvider,
saves output/voice.wav (or --output path), and prints diagnostics.

Usage:
    uv run python -m ai_content_studio.voice_runner
    uv run python -m ai_content_studio.voice_runner --voice em_alex --output output/voice_em_alex.wav
"""

import argparse
import json
import os
import struct
import sys
from pathlib import Path

from ai_content_studio.core.config import get_settings
from ai_content_studio.shared.models import Story
from ai_content_studio.video.voice.kokoro import KokoroProvider

_STORY_PATH = Path("output/story.json")
_DEFAULT_OUTPUT = Path("output/voice.wav")

_WAV_HEADER_SIZE = 44


def _wav_sample_rate(wav: bytes) -> int:
    return int(struct.unpack_from("<I", wav, 24)[0])


def _wav_duration(wav: bytes) -> float:
    sample_rate = int(struct.unpack_from("<I", wav, 24)[0])
    num_channels = int(struct.unpack_from("<H", wav, 22)[0])
    bits_per_sample = int(struct.unpack_from("<H", wav, 34)[0])
    bytes_per_sample = bits_per_sample // 8
    data_size = len(wav) - _WAV_HEADER_SIZE
    if sample_rate == 0 or num_channels == 0 or bytes_per_sample == 0 or data_size <= 0:
        return 0.0
    return data_size / (sample_rate * num_channels * bytes_per_sample)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.voice:
        os.environ["KOKORO_VOICE"] = args.voice

    settings = get_settings()
    output_path = Path(args.output) if args.output else _DEFAULT_OUTPUT

    story = Story.model_validate(json.loads(_STORY_PATH.read_text()))
    scenes = sorted(story.scenes, key=lambda s: s.order)
    narration = "\n".join(s.narration for s in scenes if s.narration)

    lang = {"a": "American English", "b": "British English", "e": "Spanish",
            "f": "French", "h": "Hindi", "i": "Italian", "p": "Portuguese BR",
            "j": "Japanese", "z": "Mandarin"}.get(settings.kokoro_voice[0], "Unknown")

    print(f"Voice:    {settings.kokoro_voice}")
    print(f"Language: {lang}")
    print(f"Speed:    {settings.kokoro_speed}")
    print(f"Chars:    {len(narration)}\n")
    print("Synthesizing...")

    provider = KokoroProvider()
    try:
        audio = provider.generate(narration)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio)

    sample_rate = _wav_sample_rate(audio)
    duration = _wav_duration(audio)

    print(f"\nSample rate: {sample_rate} Hz")
    print(f"Duration:    {duration:.2f}s")
    print(f"File size:   {len(audio) // 1024} KB")
    print(f"Output:      {output_path}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        print("ERROR: output file missing or empty")
        sys.exit(1)
    if duration <= 0:
        print("ERROR: duration is 0 — invalid WAV")
        sys.exit(1)

    print("\nOK: WAV valid")


if __name__ == "__main__":
    main()
