"""SubtitleGenerator — derives subtitle cues from scene narration text."""

import re

from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.timeline import SubtitleCue, Timeline

_MAX_CHARS = 84  # 2 lines × 42 chars
_MIN_SCENE_DURATION = 2.0


class SubtitleGenerator:
    """Generates deterministic subtitle cues from Timeline narration text."""

    def generate(self, timeline: Timeline) -> list[SubtitleCue]:
        """Derive subtitle cues from each Scene's narration, timed to the Timeline."""
        cues: list[SubtitleCue] = []
        timings = _extract_scene_timings(timeline)
        for ts, (start, end) in zip(timeline.scenes, timings, strict=True):
            cues.extend(_cues_for_scene(ts.scene, start, end))
        return cues


def _extract_scene_timings(timeline: Timeline) -> list[tuple[float, float]]:
    timings: list[tuple[float, float]] = []
    cursor = 0.0
    for ts in timeline.scenes:
        if ts.assets:
            start = ts.assets[0].start_time
            end = ts.assets[0].end_time
        else:
            duration = _narration_duration(ts.scene.narration)
            start = cursor
            end = cursor + duration
        timings.append((start, end))
        cursor = end
    return timings


def _narration_duration(narration: str) -> float:
    return max(len(narration.split()) * 0.4, _MIN_SCENE_DURATION)


def _cues_for_scene(scene: Scene, start: float, end: float) -> list[SubtitleCue]:
    narration = scene.narration.strip()
    if not narration:
        return []

    chunks = _split_into_chunks(narration)
    if not chunks:
        return []

    duration = end - start
    total_chars = sum(len(c) for c in chunks)
    cues: list[SubtitleCue] = []
    cursor = start

    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            cue_end = end
        else:
            cue_end = round(cursor + duration * (len(chunk) / total_chars), 4)
        cues.append(SubtitleCue(text=chunk, start_time=cursor, end_time=cue_end))
        cursor = cue_end

    return cues


def _split_into_chunks(text: str) -> list[str]:
    sentences = _split_sentences(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > _MAX_CHARS:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_text(sentence))
        elif not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= _MAX_CHARS:
            current = current + " " + sentence
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def _split_sentences(text: str) -> list[str]:
    return [p for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def _split_long_text(text: str) -> list[str]:
    parts = re.split(r"(?<=[,;])\s+", text)
    if len(parts) > 1:
        return _merge_parts(parts)
    return _split_by_words(text)


def _merge_parts(parts: list[str]) -> list[str]:
    chunks: list[str] = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) > _MAX_CHARS:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_by_words(part))
        elif not current:
            current = part
        elif len(current) + 1 + len(part) <= _MAX_CHARS:
            current = current + " " + part
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def _split_by_words(text: str) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current_words: list[str] = []
    current_len = 0

    for word in words:
        add_len = len(word) + (1 if current_words else 0)
        if current_len + add_len <= _MAX_CHARS:
            current_words.append(word)
            current_len += add_len
        else:
            if current_words:
                chunks.append(" ".join(current_words))
            current_words = [word]
            current_len = len(word)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
