"""Tests for PromptBuilder."""

from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.prompts import load_story_prompt
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.shared.models import CreativeBrief
from ai_content_studio.shared.models.emotion import Emotion

_STUB_BRAND = BrandContext(
    brand_document="stub brand identity content",
    mascot_document="stub mascot content",
)


def _make_brief(idea: str = "cocoa origin") -> CreativeBrief:
    return CreativeBrief(
        idea=idea,
        primary_emotion=Emotion.NOSTALGIA,
        theme="origin and legacy",
        narrative_arc="four-phase arc",
        target_duration_seconds=60,
    )


def _make_builder() -> PromptBuilder:
    return PromptBuilder(brand_context=_STUB_BRAND)


def test_prompt_contains_brand_document() -> None:
    builder = _make_builder()
    result = builder.build_story_prompt(_make_brief())
    assert _STUB_BRAND.brand_document in result


def test_prompt_contains_story_prompt() -> None:
    builder = _make_builder()
    result = builder.build_story_prompt(_make_brief())
    assert load_story_prompt() in result


def test_prompt_contains_idea() -> None:
    builder = _make_builder()
    result = builder.build_story_prompt(_make_brief("the first cocoa harvest"))
    assert "the first cocoa harvest" in result


def test_prompt_contains_primary_emotion() -> None:
    builder = _make_builder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert brief.primary_emotion.value in result


def test_prompt_contains_theme() -> None:
    builder = _make_builder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert brief.theme in result


def test_prompt_contains_narrative_arc() -> None:
    builder = _make_builder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert brief.narrative_arc in result


def test_prompt_contains_target_duration() -> None:
    builder = _make_builder()
    brief = _make_brief()
    result = builder.build_story_prompt(brief)
    assert str(brief.target_duration_seconds) in result


def test_prompt_order_brand_before_story() -> None:
    builder = _make_builder()
    result = builder.build_story_prompt(_make_brief())
    brand_pos = result.index(_STUB_BRAND.brand_document)
    story_pos = result.index(load_story_prompt())
    assert brand_pos < story_pos


def test_prompt_order_story_before_brief() -> None:
    builder = _make_builder()
    brief = _make_brief("a unique idea string")
    result = builder.build_story_prompt(brief)
    story_pos = result.index(load_story_prompt())
    idea_pos = result.index(brief.idea)
    assert story_pos < idea_pos


def test_repeated_calls_are_identical() -> None:
    builder = _make_builder()
    brief = _make_brief("a repeated idea")
    assert builder.build_story_prompt(brief) == builder.build_story_prompt(brief)


def test_different_ideas_produce_different_prompts() -> None:
    builder = _make_builder()
    assert builder.build_story_prompt(_make_brief("idea one")) != builder.build_story_prompt(
        _make_brief("idea two")
    )


def test_default_builder_uses_brand_context() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt(_make_brief())
    assert "Cocoa Talk" in result
