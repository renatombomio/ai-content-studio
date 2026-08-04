"""Tests for ReflectionDirector."""

from ai_content_studio.brain.reflection_director import ReflectionDirector
from ai_content_studio.shared.models.creative_brief import CreativeBrief
from ai_content_studio.shared.models.editorial import ContentType, EditorialPillar
from ai_content_studio.shared.models.emotion import Emotion


def test_direct_returns_creative_brief() -> None:
    director = ReflectionDirector()
    brief = director.direct("El primer silencio")
    assert isinstance(brief, CreativeBrief)


def test_direct_preserves_idea() -> None:
    director = ReflectionDirector()
    brief = director.direct("El primer silencio")
    assert brief.idea == "El primer silencio"


def test_direct_default_pillar_is_shadow_work() -> None:
    director = ReflectionDirector()
    brief = director.direct("idea")
    assert brief.pillar == EditorialPillar.SHADOW_WORK


def test_direct_accepts_custom_pillar() -> None:
    director = ReflectionDirector()
    brief = director.direct("idea", pillar=EditorialPillar.MENTAL_HEALTH)
    assert brief.pillar == EditorialPillar.MENTAL_HEALTH


def test_direct_content_type_is_video() -> None:
    director = ReflectionDirector()
    brief = director.direct("idea")
    assert brief.content_type == ContentType.VIDEO


def test_direct_target_duration_is_short() -> None:
    director = ReflectionDirector()
    brief = director.direct("idea")
    assert 10 <= brief.target_duration_seconds <= 15


def test_direct_default_language_is_spanish() -> None:
    director = ReflectionDirector()
    brief = director.direct("idea")
    assert brief.language == "es"


def test_direct_accepts_custom_emotion() -> None:
    director = ReflectionDirector()
    brief = director.direct("idea", emotion=Emotion.GRIEF)
    assert brief.primary_emotion == Emotion.GRIEF
