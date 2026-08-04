"""Tests for QuestionParser."""

import json

import pytest

from ai_content_studio.brain.question_parser import QuestionParser
from ai_content_studio.core.exceptions import ValidationError
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.shared.models.question import CocoaQuestion

_VALID_JSON = json.dumps({
    "question_text": "¿Qué parte de ti decidiste esconder para que alguien se quedara?",
    "context": "No siempre lo que guardamos nos protege. A veces protege al otro.",
    "caption": "La pregunta que no te has atrevido a hacerte.",
    "hashtags": ["#shadowwork", "#introspección"],
})

_VALID_JSON_FENCED = f"```json\n{_VALID_JSON}\n```"


def test_parse_returns_cocoa_question() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON)
    assert isinstance(result, CocoaQuestion)


def test_parse_question_text_preserved() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON)
    assert "esconder" in result.question_text


def test_parse_context_preserved() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON)
    assert "protege" in result.context


def test_parse_caption_preserved() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON)
    assert "pregunta" in result.caption


def test_parse_hashtags_preserved() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON)
    assert "#shadowwork" in result.hashtags


def test_parse_sets_pillar() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON, pillar=EditorialPillar.MENTAL_HEALTH)
    assert result.pillar == EditorialPillar.MENTAL_HEALTH


def test_parse_strips_markdown_fences() -> None:
    parser = QuestionParser()
    result = parser.parse(_VALID_JSON_FENCED)
    assert isinstance(result, CocoaQuestion)


def test_parse_raises_on_malformed_json() -> None:
    parser = QuestionParser()
    with pytest.raises(ValidationError, match="Malformed JSON"):
        parser.parse("not valid json {{{")


def test_parse_raises_on_missing_required_field() -> None:
    parser = QuestionParser()
    incomplete = json.dumps({"question_text": "¿test?"})
    with pytest.raises(ValidationError, match="validation failed"):
        parser.parse(incomplete)
