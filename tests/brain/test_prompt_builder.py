"""Tests for PromptBuilder."""

from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.prompts import load_story_prompt, load_system_prompt
from ai_content_studio.shared.models import CreativeBrief
from ai_content_studio.shared.models.emotion import Emotion


def _make_brief(idea: str = "cocoa origin") -> CreativeBrief:
    return CreativeBrief(
        idea=idea,
        primary_emotion=Emotion.NOSTALGIA,
        theme="origin and legacy",
        narrative_arc="four-phase arc",
        target_duration_seconds=60,
    )


def test_prompt_contains_system_prompt() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt(_make_brief())
    assert load_system_prompt() in result


def test_prompt_contains_story_prompt() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt(_make_brief())
    assert load_story_prompt() in result


def test_prompt_contains_idea() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt(_make_brief("the first cocoa harvest"))
    assert "the first cocoa harvest" in result


def test_prompt_contains_primary_emotion() -> None:
    builder = PromptBuilder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert brief.primary_emotion.value in result


def test_prompt_contains_theme() -> None:
    builder = PromptBuilder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert brief.theme in result


def test_prompt_contains_narrative_arc() -> None:
    builder = PromptBuilder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert brief.narrative_arc in result


def test_prompt_contains_target_duration() -> None:
    builder = PromptBuilder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert str(brief.target_duration_seconds) in result


def test_prompt_order_system_before_story() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt(_make_brief())
    system_pos = result.index(load_system_prompt())
    story_pos = result.index(load_story_prompt())
    assert system_pos < story_pos


def test_prompt_order_story_before_brief() -> None:
    builder = PromptBuilder()
    brief = _make_brief("a unique idea string")
    result = builder.build_story_prompt(brief)
    story_pos = result.index(load_story_prompt())
    idea_pos = result.index(brief.idea)
    assert story_pos < idea_pos


def test_repeated_calls_are_identical() -> None:
    builder = PromptBuilder()
    brief = _make_brief("a repeated idea")
    assert builder.build_story_prompt(brief) == builder.build_story_prompt(brief)


def test_different_ideas_produce_different_prompts() -> None:
    builder = PromptBuilder()
    assert builder.build_story_prompt(_make_brief("idea one")) != builder.build_story_prompt(
        _make_brief("idea two")
    )
