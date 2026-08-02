"""Tests for StoryParser."""

import json

import pytest

from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.core.exceptions import ValidationError
from ai_content_studio.shared.models import Story

_VALID_STORY = {
    "title": "The Last Cup",
    "hook": "She made coffee every morning for two people, long after one of them was gone.",
    "caption": "Some habits outlive the reasons we started them.",
    "hashtags": ["#CocoaTalk", "#Grief"],
    "scenes": [
        {
            "order": 1,
            "narration": "The kitchen at 6am. Two mugs on the counter.",
            "visual_prompt": "Close-up of two ceramic mugs, steam rising, morning light through a window.",
            "emotion": "longing",
            "duration_seconds": 5.0,
        }
    ],
}


def test_valid_json_returns_story() -> None:
    parser = StoryParser()
    story = parser.parse(json.dumps(_VALID_STORY))
    assert isinstance(story, Story)
    assert story.title == "The Last Cup"


def test_valid_story_scenes_are_parsed() -> None:
    parser = StoryParser()
    story = parser.parse(json.dumps(_VALID_STORY))
    assert len(story.scenes) == 1
    assert story.scenes[0].order == 1


def test_malformed_json_raises_validation_error() -> None:
    parser = StoryParser()
    with pytest.raises(ValidationError):
        parser.parse("{not valid json")


def test_missing_required_field_raises_validation_error() -> None:
    parser = StoryParser()
    incomplete = {k: v for k, v in _VALID_STORY.items() if k != "title"}
    with pytest.raises(ValidationError):
        parser.parse(json.dumps(incomplete))


def test_wrong_field_type_raises_validation_error() -> None:
    parser = StoryParser()
    bad = {**_VALID_STORY, "scenes": "not a list"}
    with pytest.raises(ValidationError):
        parser.parse(json.dumps(bad))


def test_empty_string_raises_validation_error() -> None:
    parser = StoryParser()
    with pytest.raises(ValidationError):
        parser.parse("")


def test_parse_is_deterministic() -> None:
    parser = StoryParser()
    raw = json.dumps(_VALID_STORY)
    story_a = parser.parse(raw)
    story_b = parser.parse(raw)
    assert story_a.title == story_b.title
    assert story_a.hook == story_b.hook
    assert len(story_a.scenes) == len(story_b.scenes)
