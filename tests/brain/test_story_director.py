"""Tests for StoryDirector."""

from ai_content_studio.brain.story_director import StoryDirector
from ai_content_studio.shared.models import CreativeBrief, Emotion


def test_direct_returns_creative_brief() -> None:
    director = StoryDirector()
    result = director.direct("a farmer who plants cocoa for a future he will not see")
    assert isinstance(result, CreativeBrief)


def test_direct_idea_is_preserved() -> None:
    director = StoryDirector()
    idea = "the last cup of coffee"
    brief = director.direct(idea)
    assert brief.idea == idea


def test_direct_primary_emotion_is_self_discovery() -> None:
    director = StoryDirector()
    brief = director.direct("any idea")
    assert brief.primary_emotion == Emotion.SELF_DISCOVERY


def test_direct_theme_equals_idea() -> None:
    director = StoryDirector()
    idea = "a letter never sent"
    brief = director.direct(idea)
    assert brief.theme == idea


def test_direct_narrative_arc_is_correct() -> None:
    director = StoryDirector()
    brief = director.direct("any idea")
    assert brief.narrative_arc == "recognition-conflict-reflection-resonance"


def test_direct_target_duration_is_60() -> None:
    director = StoryDirector()
    brief = director.direct("any idea")
    assert brief.target_duration_seconds == 60


def test_direct_is_deterministic() -> None:
    director = StoryDirector()
    idea = "the weight of small decisions"
    assert director.direct(idea).model_dump() == director.direct(idea).model_dump()
