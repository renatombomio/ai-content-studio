"""Tests for ReflectionParser."""

import json

import pytest

from ai_content_studio.brain.reflection_parser import ReflectionParser
from ai_content_studio.core.exceptions import ValidationError
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.shared.models.reflection import Reflection

_VALID_JSON = json.dumps({
    "title": "El primer silencio",
    "reflection_text": "Hubo un día en que decidiste que tu dolor no merecía espacio.",
    "caption": "A veces el primer silencio es el que más pesa.",
    "visual_prompt": "Close-up of a child's hand letting go of another hand. Warm afternoon light. Shallow depth of field.",
    "hashtags": ["#shadowwork", "#sanacioninterior"],
})

_VALID_JSON_FENCED = f"```json\n{_VALID_JSON}\n```"


def test_parse_returns_reflection() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON)
    assert isinstance(result, Reflection)


def test_parse_reflection_text_preserved() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON)
    assert "decidiste" in result.reflection_text


def test_parse_visual_prompt_preserved() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON)
    assert "child" in result.visual_prompt


def test_parse_title_preserved() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON)
    assert result.title == "El primer silencio"


def test_parse_hashtags_preserved() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON)
    assert "#shadowwork" in result.hashtags


def test_parse_caption_preserved() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON)
    assert "silencio" in result.caption


def test_parse_caption_defaults_to_empty() -> None:
    parser = ReflectionParser()
    no_caption = json.dumps({
        "title": "test",
        "reflection_text": "Texto.",
        "visual_prompt": "A scene.",
        "hashtags": [],
    })
    result = parser.parse(no_caption)
    assert result.caption == ""


def test_parse_sets_pillar() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON, pillar=EditorialPillar.MENTAL_HEALTH)
    assert result.pillar == EditorialPillar.MENTAL_HEALTH


def test_parse_sets_language() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON, language="es")
    assert result.language == "es"


def test_parse_strips_markdown_fences() -> None:
    parser = ReflectionParser()
    result = parser.parse(_VALID_JSON_FENCED)
    assert isinstance(result, Reflection)


def test_parse_raises_on_malformed_json() -> None:
    parser = ReflectionParser()
    with pytest.raises(ValidationError, match="Malformed JSON"):
        parser.parse("not valid json {{{")


def test_parse_raises_on_missing_required_field() -> None:
    parser = ReflectionParser()
    incomplete = json.dumps({"title": "test"})
    with pytest.raises(ValidationError, match="validation failed"):
        parser.parse(incomplete)
