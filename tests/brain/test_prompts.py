"""Tests for Brain prompt files."""

from ai_content_studio.brain.prompts import (
    STORY_PROMPT_PATH,
    SYSTEM_PROMPT_PATH,
    load_story_prompt,
    load_system_prompt,
)


def test_system_prompt_file_exists() -> None:
    assert SYSTEM_PROMPT_PATH.exists()


def test_story_prompt_file_exists() -> None:
    assert STORY_PROMPT_PATH.exists()


def test_system_prompt_is_readable() -> None:
    content = load_system_prompt()
    assert isinstance(content, str)


def test_story_prompt_is_readable() -> None:
    content = load_story_prompt()
    assert isinstance(content, str)


def test_system_prompt_is_not_empty() -> None:
    assert len(load_system_prompt().strip()) > 0


def test_story_prompt_is_not_empty() -> None:
    assert len(load_story_prompt().strip()) > 0
