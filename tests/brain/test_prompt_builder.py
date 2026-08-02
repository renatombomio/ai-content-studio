"""Tests for PromptBuilder."""

from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.prompts import load_story_prompt, load_system_prompt


def test_prompt_contains_system_prompt() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt("cocoa origin")
    assert load_system_prompt() in result


def test_prompt_contains_story_prompt() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt("cocoa origin")
    assert load_story_prompt() in result


def test_prompt_contains_idea() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt("the first cocoa harvest")
    assert "the first cocoa harvest" in result


def test_prompt_order_system_before_story() -> None:
    builder = PromptBuilder()
    result = builder.build_story_prompt("any idea")
    system_pos = result.index(load_system_prompt())
    story_pos = result.index(load_story_prompt())
    assert system_pos < story_pos


def test_prompt_order_story_before_idea() -> None:
    builder = PromptBuilder()
    idea = "a unique idea string"
    result = builder.build_story_prompt(idea)
    story_pos = result.index(load_story_prompt())
    idea_pos = result.index(idea)
    assert story_pos < idea_pos


def test_repeated_calls_are_identical() -> None:
    builder = PromptBuilder()
    idea = "a repeated idea"
    assert builder.build_story_prompt(idea) == builder.build_story_prompt(idea)


def test_different_ideas_produce_different_prompts() -> None:
    builder = PromptBuilder()
    assert builder.build_story_prompt("idea one") != builder.build_story_prompt("idea two")
